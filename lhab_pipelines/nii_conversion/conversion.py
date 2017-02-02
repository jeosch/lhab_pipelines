import datetime as dt
import os
from glob import glob

from nipype.interfaces.dcm2nii import Dcm2niix
from nipype.interfaces.fsl import Reorient2Std

import lhab_pipelines
from lhab_pipelines.utils import add_info_to_json
from .utils import get_public_sub_id, get_clean_ses_id, get_clean_subject_id, \
    update_sub_scans_file, deface_data, dwi_treat_bvecs, add_additional_bids_parameters_from_par, \
    add_flip_angle_from_par, add_total_readout_time_from_par, parse_physio, save_physio


def submit_single_subject(old_subject_id, ses_id_list, raw_dir, in_ses_folder, output_dir, info_list,
                          bvecs_from_scanner_file=None, public_output=True, use_new_ids=True,
                          new_id_lut_file=None):
    """
    Loops through raw folders and identifies old_subject_id in tps.
    Pipes available tps into convert_modality
    public_output: if True: strips all info about original subject_id, file, date
    use_new_ids: if True, uses new id from mapping file
    """
    if public_output:
        assert use_new_ids, "Public output requested, but retaining old subject ids; Doesn't sound good."

    some_data_found = False
    for old_ses_id in ses_id_list:
        subject_ses_folder = os.path.join(raw_dir, old_ses_id, in_ses_folder)
        os.chdir(subject_ses_folder)
        subject_folder = sorted(glob(old_subject_id + "*"))
        assert len(subject_folder) < 2, "more than one subject folder %s" % old_subject_id

        if subject_folder:
            some_data_found = True
            subject_folder = subject_folder[0]
            abs_subject_folder = os.path.abspath(subject_folder)
            os.chdir(abs_subject_folder)

            if use_new_ids:
                public_sub_id = get_public_sub_id(old_subject_id, new_id_lut_file)
            else:
                public_sub_id = None

            for infodict in info_list:
                convert_modality(old_subject_id,
                                 old_ses_id,
                                 output_dir,
                                 bvecs_from_scanner_file=bvecs_from_scanner_file,
                                 public_sub_id=public_sub_id,
                                 public_output=public_output,
                                 **infodict)

    if not some_data_found:
        raise FileNotFoundError("No data found for %s. Check again. Stopping..." % old_subject_id)


def convert_modality(old_subject_id, old_ses_id, output_dir, bids_name, bids_modality,
                     search_str, bvecs_from_scanner_file=None, public_sub_id=None, public_output=True,
                     reorient2std=True, task=None, direction=None, acq=None,
                     only_use_last=False, deface=False, physio=False, add_info={}):
    """
    runs conversion for one subject and one modality
    public_output: if True: strips all info about original subject_id, file, date
    """
    if (public_output and bids_modality == "anat" and not deface):
        raise Exception("Public output requested, but anatomical images not defaced. exit. %s %s %s" % (
            old_subject_id, old_ses_id, bids_name))

    new_ses_id = get_clean_ses_id(old_ses_id)
    bids_ses = "ses-" + new_ses_id
    if public_sub_id:
        bids_sub = "sub-" + public_sub_id
    else:
        bids_sub = "sub-" + get_clean_subject_id(old_subject_id)
    mapping_file = os.path.join(output_dir, bids_sub, "par2nii_mapping.txt")

    par_file_list = glob("*" + search_str + "*.par")
    if par_file_list:
        sub_output_dir = os.path.join(output_dir, bids_sub)
        nii_output_dir = os.path.join(sub_output_dir, bids_ses, bids_modality)

        if not os.path.exists(nii_output_dir):
            os.makedirs(nii_output_dir)

        if only_use_last:
            par_file_list = par_file_list[-1:]

        for run_id, par_file in enumerate(par_file_list, 1):
            # put together bids file name
            # bids run
            bids_run = "run-" + str(run_id)
            out_components = [bids_sub, bids_ses]

            # bids acq
            if acq:
                out_components += ["acq-%s" % acq]

            # bids task
            if task:
                out_components += ["task-%s" % task]

            # bids acq. direction
            if direction:
                out_components += ["dir-%s" % direction]

            out_components += [bids_run, bids_name]
            out_filename = "_".join(out_components)
            nii_file = os.path.join(nii_output_dir, out_filename + ".nii.gz")
            assert not os.path.exists(nii_file), "file exists. STOP. %s" % nii_file

            bids_file, converter_results = run_dcm2niix(bids_name, bids_modality, bvecs_from_scanner_file,
                                                        mapping_file, nii_file, nii_output_dir, out_filename, par_file,
                                                        public_output, task)

            if reorient2std:
                reorient = Reorient2Std()
                reorient.inputs.in_file = converter_results.outputs.converted_files
                reorient.inputs.out_file = converter_results.outputs.converted_files
                reorient_results = reorient.run()

            if deface:
                deface_data(nii_file, nii_output_dir, out_filename)
            add_info_to_json(bids_file, {"Defaced": deface})

            add_info_to_json(bids_file, add_info)

            update_sub_scans_file(output_dir, bids_sub, bids_ses, bids_modality, out_filename, par_file, public_output)

            # finally as a sanity check, check that converted nii exists
            assert os.path.exists(nii_file), "Something went wrong" \
                                             "converted file does not exist. STOP. %s" % nii_file

            if physio:  # convert physiological data
                physio_search_str = ".".join(par_file.split(".")[:-1]) + "_physio.log"
                physio_in_file_list = glob(physio_search_str)
                assert len(physio_in_file_list) < 2, "more than 1  phyio file found for %s" % physio_search_str

                if physio_in_file_list:
                    physio_out_file_base = os.path.join(nii_output_dir, out_filename + "_physio")
                    meta_data, physio_data = parse_physio(physio_in_file_list[0])
                    save_physio(physio_out_file_base, meta_data, physio_data)


def run_dcm2niix(bids_name, bids_modality, bvecs_from_scanner_file, mapping_file, nii_file, nii_output_dir,
                 out_filename, par_file, public_output, task):
    '''
    Converts one par/rec pair to nii.gz.
    Adds scan duration and dcm2niix & docker container version to bids file.
    '''

    abs_par_file = os.path.abspath(par_file)
    abs_rec_file = os.path.splitext(abs_par_file)[0] + ".rec"

    assert os.path.exists(abs_rec_file), "REC file does not exist %s" % abs_rec_file

    # run converter
    converter = Dcm2niix()
    converter.inputs.source_names = [abs_par_file]
    converter.inputs.bids_format = True
    converter.inputs.compress = 'i'
    converter.inputs.has_private = True
    converter.inputs.out_filename = out_filename
    converter.inputs.output_dir = nii_output_dir
    print("XXXXXXX running dcm2niix command")
    print(converter.cmdline)
    converter_results = converter.run()
    bids_file = converter_results.outputs.bids

    # add additional information to json
    ## scan duration
    add_additional_bids_parameters_from_par(abs_par_file, bids_file, {"scan_duration": "ScanDurationSec",
                                                                      "technique": "PulseSequenceType",
                                                                      "protocol_name": "PulseSequenceDetails"})

    add_flip_angle_from_par(abs_par_file, bids_file)
    add_total_readout_time_from_par(abs_par_file, bids_file)

    ## lhab_pipelines
    add_info_to_json(bids_file, {"LhabPipelinesVersion": lhab_pipelines.__version__})

    ## task
    if task:
        add_info_to_json(bids_file, {"TaskName": task})

    ## time
    add_info_to_json(bids_file, {"ConversionTimestamp": str(dt.datetime.now())})

    if not public_output:
        # write par 2 nii mapping file only for private use
        with open(mapping_file, "a") as fi:
            fi.write("%s %s\n" % (abs_par_file, nii_file))
    else:
        # remove info file generated by dcm2niix
        os.remove(os.path.join(nii_output_dir, out_filename + '.txt'))

    # rotate bvecs and add angulation to json for dwi
    if (bids_name == "dwi") & (bids_modality != "fmap"):
        dwi_treat_bvecs(abs_par_file, bids_file, bvecs_from_scanner_file, nii_output_dir, par_file)
        # remove _dwi_ADC.nii.gz file created by dcm2niix
        adc_file = glob(os.path.join(nii_output_dir, "*_dwi_ADC.nii.gz"))[0]
        os.remove(adc_file)

    return bids_file, converter_results
