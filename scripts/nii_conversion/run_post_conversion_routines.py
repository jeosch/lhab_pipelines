"""
- export demos
- Collects scan durations for resting state
- Checks that all subjects are present and compare par and nii count, export nii count
- Reduces scans file
- Calculates session durations
"""

import os
from lhab_pipelines.utils import read_tsv
from lhab_pipelines.nii_conversion.post_conversion_utils import calc_demos, calc_session_duration, get_scan_duration, \
    compare_par_nii, reduce_sub_files

import argparse
import getpass

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('raw_dir', help='The directory with the RAW input dataset.'
                                        '\n original: bids_dir')
    parser.add_argument('output_base_dir', help='The directory where the output files '
                                                'should be stored.'
                                                '\n original: output_dir')
    parser.add_argument('--participant_file', help='participants that should be analyzed.'
                                                   'For the conversion wf this should be given as lhab_1234')

    parser.add_argument('--no-public_output',
                        help="Don't create public output.\nIf public_output: strips all info about original "
                             "subject_id, file, date \nDefault: use public_output",
                        default=True, dest="public_output", action='store_false')
    parser.add_argument('--no-use_new_ids', help="Don't use new subject ids. "
                                                 "\nDefault: Use new ids from mapping file",
                        default=True, dest="use_new_ids", action='store_false')
    parser.add_argument('--ds_version', help="Data set version (is added to output path)", default="dev")

    args = parser.parse_args()

    raw_dir = args.raw_dir

    # privacy settings
    public_output = args.public_output
    use_new_ids = args.use_new_ids
    if not (public_output and use_new_ids):
        private_str = "_PRIVATE"
    else:
        private_str = ""

    output_dir = os.path.join(args.output_base_dir, "LHAB_" + args.ds_version + private_str, "sourcedata")

    ###
    if args.participant_file:
        old_sub_id_list = read_tsv(args.participant_file)["subject_id"].tolist()
    else:
        raise Exception("No subjects specified")

    ses_id_list = ["T1", "T2", "T3", "T4", "T5"]
    in_ses_folder = "01_noIF"
    new_id_lut_file = os.path.join(raw_dir, "00_PRIVATE_sub_lists/new_sub_id_lut.tsv")
    demo_file = os.path.join(raw_dir, "00_PRIVATE_sub_lists/dob.zip")

    #
    pwd = getpass.getpass("Enter the Password for dob file:")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)


    info_list = [
        {"bids_name": "T1w", "bids_modality": "anat", "search_str": "_t1w_"},
        {"bids_name": "FLAIR", "bids_modality": "anat", "search_str": "_2dflair_", "acq": "2D"},
        {"bids_name": "FLAIR", "bids_modality": "anat", "search_str": "_3dflair_", "acq": "3D"},
        {"bids_name": "dwi", "bids_modality": "dwi", "search_str": "_dti_T", "only_use_last": True, "direction": "ap"},
        {"bids_name": "bold", "bids_modality": "func", "search_str": "_fmri_T", "task": "rest", "physio": True},
        {"bids_name": "bold", "bids_modality": "fmap", "search_str": "_fmri_pa_T", "direction": "pa"},
        {"bids_name": "dwi", "bids_modality": "fmap", "search_str": "_dti_pa_T", "direction": "pa"},
        {"bids_name": "dwi", "bids_modality": "fmap", "search_str": "_dti_ap_T", "direction": "ap"}

    ]



    print("Exporting demos...")
    calc_demos(output_dir,
               ses_id_list,
               raw_dir,
               in_ses_folder,
               demo_file,
               pwd,
               use_new_ids=use_new_ids,
               new_id_lut_file=new_id_lut_file,
               public_output=public_output,
               )

    print("Collecting scan durations...")
    get_scan_duration(output_dir)

    print("\n Check that all subjecst are present and compare par and nii count, export nii count...")
    compare_par_nii(output_dir, old_sub_id_list, raw_dir, ses_id_list, in_ses_folder, info_list, new_id_lut_file)

    print("\nReducing scans file...")
    reduce_sub_files(output_dir, "scans.tsv", "scans.tsv")


    if not (public_output and use_new_ids):
        print("\nCalculating session durations...")
        calc_session_duration(output_dir, public_output, use_new_ids)
