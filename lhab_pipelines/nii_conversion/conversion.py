import os
from glob import glob
import datetime as dt
from joblib import Parallel, delayed
import pandas as pd

from lhab_pipelines.utils import add_info_to_json
from .utils import get_public_sub_id, get_new_ses_id, get_new_subject_id, \
    update_sub_scans_file, deface_data, dwi_treat_bvecs, add_additional_bids_parameters_from_par
from ..utils import get_docker_container_name, read_tsv

from nipype.interfaces.dcm2nii import Dcm2niix
from nipype.interfaces.fsl import Reorient2Std
import datetime as dt


def convert_subjects(old_sub_id_list,
                     ses_id_list,
                     raw_dir,
                     in_ses_folder,
                     output_dir,
                     info_list,
                     bvecs_from_scanner_file=None,
                     public_output=True,
                     use_new_ids=True,
                     face_dir=None,
                     new_id_lut_file=None,
                     dob_file=None,
                     n_jobs=-1):
    '''
    Parallelized submit call over subjects
    public_output: if True: strips all info about original subject_id, file, date
    use_new_ids: if True, uses new id from mapping file
    '''
    info_file = os.path.join(output_dir, "..", "info.txt")
    s = "\n%s" % dt.datetime.now()
    s += "\npublic_output: %s" % public_output
    s += "\nuse_new_ids: %s" % public_output
    s += "\ninfo_list: %s" % info_list

    with open(info_file, "a") as fi:
        fi.write(s)

    Parallel(n_jobs=n_jobs)(
        delayed(submit_single_subject)(old_subject_id,
                                       ses_id_list,
                                       raw_dir,
                                       in_ses_folder,
                                       output_dir,
                                       info_list,
                                       bvecs_from_scanner_file=bvecs_from_scanner_file,
                                       public_output=public_output,
                                       use_new_ids=use_new_ids,
                                       face_dir=face_dir,
                                       new_id_lut_file=new_id_lut_file,
                                       dob_file=dob_file) for old_subject_id in
        old_sub_id_list)


def submit_single_subject(old_subject_id, ses_id_list, raw_dir, in_ses_folder, output_dir, info_list,
                          bvecs_from_scanner_file=None, public_output=True, use_new_ids=True,
                          face_dir=None, new_id_lut_file=None, dob_file=None):
    """
    Loops through raw folders and identifies old_subject_id in tps.
    Pipes available tps into convert_modality
    public_output: if True: strips all info about original subject_id, file, date
    use_new_ids: if True, uses new id from mapping file
    """
    if public_output:
        assert use_new_ids, "Public output requested, but retaining old subject ids; Doesn't sound good."

    # get dob
    # FIXME
    if dob_file:
        dob_df = read_tsv(dob_file)
        dob_df.set_index("sub_id", inplace=True)
        pd.to_datetime(dob_df["dob"], format="%Y-%m-%d")
        dob = dob_df.loc[old_subject_id, "dob"]
    else:
        dob = None

    for old_ses_id in ses_id_list:
        subject_ses_folder = os.path.join(raw_dir, old_ses_id, in_ses_folder)
        os.chdir(subject_ses_folder)
        subject_folder = sorted(glob(old_subject_id + "*"))
        assert len(subject_folder) < 2, "more than one subject folder %s" % old_subject_id

        if subject_folder:
            subject_folder = subject_folder[0]
            abs_subject_folder = os.path.abspath(subject_folder)
            os.chdir(abs_subject_folder)

            if use_new_ids:
                public_sub_id = get_public_sub_id(old_subject_id, new_id_lut_file)
            else:
                public_sub_id = None

            # calculate dob

            for infodict in info_list:
                convert_modality(old_subject_id,
                                 old_ses_id,
                                 output_dir,
                                 bvecs_from_scanner_file=bvecs_from_scanner_file,
                                 public_sub_id=public_sub_id,
                                 public_output=public_output,
                                 face_dir=face_dir,
                                 **infodict)


def convert_modality(old_subject_id, old_ses_id, output_dir, bids_name, bids_modality,
                     search_str, bvecs_from_scanner_file=None, public_sub_id=None, public_output=True, face_dir=None,
                     reorient2std=True, task=None, direction=None,
                     only_use_last=False, deface=False):
    """
    runs conversion for one subject and one modality
    public_output: if True: strips all info about original subject_id, file, date
    """

    new_ses_id = get_new_ses_id(old_ses_id)
    bids_ses = "ses-" + new_ses_id
    if public_sub_id:
        bids_sub = "sub-" + public_sub_id
    else:
        bids_sub = "sub-" + get_new_subject_id(old_subject_id)
    mapping_file = os.path.join(output_dir, bids_sub, "par2nii_mapping.txt")

    par_file_list = glob("*" + search_str + "*.par")
    if par_file_list:
        nii_output_dir = os.path.join(output_dir, bids_sub, bids_ses, bids_modality)
        if not os.path.exists(nii_output_dir):
            os.makedirs(nii_output_dir)

        if only_use_last:
            par_file_list = par_file_list[-1:]

        for run_id, par_file in enumerate(par_file_list, 1):

            # put together bids file name
            # bids run
            bids_run = "run-" + str(run_id)
            out_components = [bids_sub, bids_ses]

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

            bids_file, converter_results = run_dcm2niix(bids_name, bvecs_from_scanner_file, mapping_file, nii_file,
                                                        nii_output_dir, out_filename, par_file, public_output, task)

            if reorient2std:
                reorient = Reorient2Std()
                reorient.inputs.in_file = converter_results.outputs.converted_files
                reorient.inputs.out_file = converter_results.outputs.converted_files
                reorient_results = reorient.run()

            if deface:
                deface_data(bids_file, face_dir, nii_file, nii_output_dir, out_filename)

            update_sub_scans_file(output_dir, bids_sub, bids_ses, bids_modality, out_filename, par_file, public_output)

            # finally as a sanity check, check that converted nii exists
            assert os.path.exists(nii_file), "Something went wrong" \
                                             "converted file does not exist. STOP. %s" % nii_file


def run_dcm2niix(bids_name, bvecs_from_scanner_file, mapping_file, nii_file, nii_output_dir, out_filename, par_file,
                 public_output, task):
    '''
    Converts one par/rec pair to nii.gz.
    Adds scan duration and dcm2niix & docker container version to bids file.
    '''
    # fixme bug in dcm2niix requires capital letter extension .PAR .REC (Linux only)
    # abs_par_file = os.path.abspath(par_file)
    # abs_rec_file = os.path.splitext(abs_par_file)[0] + ".rec"
    parrec_name = os.path.splitext(os.path.abspath(par_file))[0]
    abs_par_file_orig = parrec_name + ".par"
    abs_rec_file_orig = parrec_name + ".rec"
    abs_par_file = parrec_name + ".PAR"
    abs_rec_file = parrec_name + ".REC"

    # try symlink; this does not work in macos hosts, where par PAR is not an issue
    try:
        os.symlink(abs_par_file_orig, abs_par_file)
    except FileExistsError:
        abs_par_file = os.path.abspath(par_file)

    try:
        os.symlink(abs_rec_file_orig, abs_rec_file)
    except:
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
    add_additional_bids_parameters_from_par(abs_par_file, bids_file, {"scan_duration": "ScanDurationSec"})

    ## dcm2niix version
    v = converter.version_from_command()
    v_start = v.find(b"version ") + 8
    dcm2niix_version = v[v_start:v_start + 10].decode("utf-8")
    add_info_to_json(bids_file, {"conversion_dcm2niix_version": dcm2niix_version})

    ## docker container version
    try:
        docker_container_name = get_docker_container_name()
        add_info_to_json(bids_file, {"conversion_docker_container_name": docker_container_name})
    except:
        pass

    ## task
    if task:
        add_info_to_json(bids_file, {"TaskName": task})

    ## time
    add_info_to_json(bids_file, {"conversion_timestamp": str(dt.datetime.now())})

    if not public_output:
        # write par 2 nii mapping file only for private use
        with open(mapping_file, "a") as fi:
            fi.write("%s %s\n" % (abs_par_file, nii_file))
    else:
        # remove info file generated by dcm2niix
        os.remove(os.path.join(nii_output_dir, out_filename + '.txt'))

    # rotate bvecs and add angulation to json for dwi
    if bids_name == "dwi":
        dwi_treat_bvecs(abs_par_file, bids_file, bvecs_from_scanner_file, nii_output_dir, par_file)
        # remove _dwi_ADC.nii.gz file created by dcm2niix
        adc_file = glob(os.path.join(nii_output_dir, "*_dwi_ADC.nii.gz"))[0]
        os.remove(adc_file)

    return bids_file, converter_results
