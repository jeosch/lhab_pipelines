from glob import glob
import os

from nipype.interfaces.dcm2nii import Dcm2niix
from nipype.interfaces.fsl import Reorient2Std

from .utils import get_public_sub_id, get_new_ses_id, get_new_subject_id, \
    add_additional_bids_parameters_from_par, update_scans_file, deface_data, dwi_rotate_bvecs
from lhab_pipelines.utils import add_info_to_json
from ..utils import get_docker_container_name

def run_conversions(old_subject_id, old_ses_id, abs_subject_folder, output_dir, info_list,
                    bvecs_from_scanner_file=None, public_output=False, face_dir=None, new_id_lut_file=None):
    """
    runs conversion for one subject for all modalities defined in info_list
    :param old_subject_id:
    :param old_ses_id:
    :param abs_subject_folder:
    :param output_dir:
    :param info_list:
    :param bvecs_from_scanner_file:
    :param public_output: if True removes sensitive information (original ids) and uses new_id_lut_file for new sub_id
    :param face_dir: contains face.gca and talairach_mixed_with_skull.gca for mri_deface
    :param new_id_lut_file: matching between old_ids and new_ids (public)
    """
    os.chdir(abs_subject_folder)
    if public_output:
        public_sub_id = get_public_sub_id(old_subject_id, new_id_lut_file)
    for infodict in info_list:
        convert_modality(old_subject_id, old_ses_id, output_dir, bvecs_from_scanner_file=bvecs_from_scanner_file,
                         public_sub_id=public_sub_id, face_dir=face_dir, **infodict)


def convert_modality(old_subject_id, old_ses_id, output_dir, bids_name, bids_modality,
                     search_str, bvecs_from_scanner_file=None, public_sub_id=None, face_dir=None,
                     reorient2std=True, task=None, direction=None,
                     only_use_last=False, deface=False):
    "runs conversion for one subject and one modality"

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
            # fixme bug in dcm2niix requires capital letter extension .PAR .REC (Linux only)
            # abs_par_file = os.path.abspath(par_file)
            # abs_rec_file = os.path.splitext(abs_par_file)[0] + ".rec"
            parrec_name = os.path.splitext(os.path.abspath(par_file))[0]
            abs_par_file_orig = parrec_name + ".par"
            abs_rec_file_orig = parrec_name + ".rec"
            abs_par_file = parrec_name + ".PAR"
            abs_rec_file = parrec_name + ".REC"

            # try symling; this does not work in macos hosts, where par PAR is not an issue
            try:
                os.symlink(abs_par_file_orig, abs_par_file)
            except FileExistsError:
                abs_par_file = os.path.abspath(par_file)

            try:
                os.symlink(abs_rec_file_orig, abs_rec_file)
            except:
                abs_rec_file = os.path.splitext(abs_par_file)[0] + ".rec"
            ##

            assert os.path.exists(abs_rec_file), "REC file does not exist %s" % abs_rec_file

            bids_run = "run-" + str(run_id)
            out_components = [bids_sub, bids_ses]
            if task:
                out_components += ["task-%s" % task]
            if direction:
                out_components += ["dir-%s" % direction]

            out_components += [bids_run, bids_name]
            out_filename = "_".join(out_components)
            nii_file = os.path.join(nii_output_dir, out_filename + ".nii.gz")
            assert not os.path.exists(nii_file), "file exists. STOP. %s" % nii_file

            converter = Dcm2niix()
            converter.inputs.source_names = [abs_par_file]
            converter.inputs.bids_format = True
            converter.inputs.compress = 'i'
            converter.inputs.has_private = True
            converter.inputs.out_filename = out_filename
            converter.inputs.output_dir = nii_output_dir
            print("XXXXXXX")
            print(converter.cmdline)
            converter_results = converter.run()
            bids_file = converter_results.outputs.bids

            # add additional information to json
            add_additional_bids_parameters_from_par(abs_par_file, bids_file, {"scan_duration": "ScanDurationSec"})

            if not public_sub_id:
                # write par 2 nii mapping file only for private use
                with open(mapping_file, "a") as fi:
                    fi.write("%s %s\n"%(abs_par_file, nii_file))
            else:
                # remove info file generated by dcm2niix
                os.remove(os.path.join(nii_output_dir, out_filename + '.txt'))

            # add angulation to json for dwi
            if bids_name == "dwi":
                dwi_rotate_bvecs(abs_par_file, bids_file, bvecs_from_scanner_file, nii_output_dir, par_file)
                # remove _dwi_ADC.nii.gz file created by dcm2niix
                adc_file = glob(os.path.join(nii_output_dir, "*_dwi_ADC.nii.gz"))[0]
                os.remove(adc_file)

            # add task and number of volumes to json file for rest
            if task:
                add_info_to_json(bids_file, {"TaskName": task})

            if reorient2std:
                reorient = Reorient2Std()
                reorient.inputs.in_file = converter_results.outputs.converted_files
                reorient.inputs.out_file = converter_results.outputs.converted_files
                reorient_results = reorient.run()

            if deface:
                deface_data(bids_file, face_dir, nii_file, nii_output_dir, out_filename)

            try:
                docker_container_name = get_docker_container_name()
                add_info_to_json(bids_file, {"conversion_docker_container_name": docker_container_name})
            except:
                pass

            # dcm2niix version
            v = converter.version_from_command()
            v_start = v.find(b"version ") + 8
            dcm2niix_version = v[v_start:v_start + 10].decode("utf-8")
            add_info_to_json(bids_file, {"conversion_dcm2niix_version": dcm2niix_version})

            update_scans_file(output_dir, bids_sub, bids_ses, bids_modality, out_filename, par_file)


