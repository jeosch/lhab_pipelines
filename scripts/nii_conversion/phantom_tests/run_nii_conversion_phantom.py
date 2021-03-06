"""
CI Test for LHAB conversion pipeline (par to nifti).
- converts example data set (phantom)
- tests if files nifti and json files are there
- tests if sensitive information is deleted
- runs bids validator

- does NOT check dwi data conversion

- docker run --rm -ti -v ${HOME}/outputs:/data/out fliem/${CIRCLE_PROJECT_REPONAME,,} python /code/lhab_pipelines/scripts/nii_conversion/phantom_tests/run_nii_conversion_phantom.py /code/lhab_pipelines/scripts/nii_conversion/phantom_tests/01_RAW /data/out participant --ds_version phantomas
"""

import os, argparse
from lhab_pipelines.utils import read_tsv, add_info_to_json
from lhab_pipelines.nii_conversion.conversion import submit_single_subject
import datetime as dt
import numpy as np
import json
from os.path import join as oj

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='LHAB raw to nifti conversion. \nBIDS-Apps compatiple arguments.'
                                                 "\nexample:\n python run_nii_conversion.py /data/raw /data/ participant "
                                                 "--no-public_output --participant_label lhab_1c")
    parser.add_argument('raw_dir', help='The directory with the RAW input dataset.'
                                        '\n original: bids_dir')
    parser.add_argument('output_base_dir', help='The directory where the output files '
                                                'should be stored.'
                                                '\n original: output_dir')
    parser.add_argument('analysis_level', help='Level of the analysis that will be performed. ',
                        choices=['participant'])
    parser.add_argument('--participant_label', help='The label of the participant that should be analyzed.'
                                                    'For the conversion wf this should be given as lhab_1234',
                        nargs="+")
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

    output_dir = oj(args.output_base_dir, "LHAB_" + args.ds_version + private_str, "sourcedata")

    ###
    if args.participant_label:
        old_sub_id_list = [s.strip() for s in args.participant_label]
        exclude_sub_id_list = "none"
    else:
        # SUBJECT ID STUFF
        all_sub_file = oj(raw_dir, "00_PRIVATE_sub_lists/phan_id_list.tsv")
        exclude_sub_file = None  # oj(raw_dir,
        # "00_PRIVATE_sub_lists/tp5_sub_exclude.tsv")

        # get subject and exclude subj list
        old_sub_id_list = read_tsv(all_sub_file)["sub_id"].tolist()

        try:
            exclude_sub_id_list = read_tsv(exclude_sub_file)["sub_id"].tolist()
            for bad in exclude_sub_id_list:
                old_sub_id_list.remove(bad)
                print("Removed %s" % bad)
        except:
            exclude_sub_id_list = "none"

    ###
    ###
    ses_id_list = ["T1", "T3"]
    in_ses_folder = "01_noIF"
    bvecs_from_scanner_file = oj(raw_dir, "00_bvecs/bvecs.fromscanner")
    new_id_lut_file = oj(raw_dir, "00_PRIVATE_sub_lists/new_sub_id_lut.tsv")

    # LAS Orientation
    # i : RL
    # i-: LR
    # j : PA
    # j-: AP
    # k : IS
    # k-: SI
    general_info = {"MagneticFieldStrength": 3.0, "ManufacturersModelName": "Philips Ingenia"}
    sense_info = {"ParallelAcquisitionTechnique": "SENSE", "ParallelReductionFactorInPlane": 2}

    # TR=2sec, 43 slices,  # ascending sliceorder
    rs_info = {"SliceEncodingDirection": "k", "SliceTiming": np.arange(0, 2.0, 2. / 43)}

    info_list = [
        # anatomical
        {"bids_name": "T1w", "bids_modality": "anat", "search_str": "_t1w_", "deface": True,
         "add_info": {**general_info}},
        # flair
        {"bids_name": "FLAIR", "bids_modality": "anat", "search_str": "_2dflair_", "acq": "2D", "deface": True,
         "add_info": {**general_info}},
        {"bids_name": "FLAIR", "bids_modality": "anat", "search_str": "_3dflair_", "acq": "3D", "deface": True,
         "add_info": {**general_info}},

        # dwi
        {"bids_name": "dwi", "bids_modality": "dwi", "search_str": "_dti_T", "only_use_last": True, "acq": "ap",
         "add_info": {**general_info, **sense_info, "PhaseEncodingDirection": "j-"}},

        # func
        {"bids_name": "bold", "bids_modality": "func", "search_str": "_fmri_T", "task": "rest", "physio": True,
         "add_info": {**general_info, **sense_info, **rs_info, "PhaseEncodingDirection": "j-"}},

        # fieldmaps
        {"bids_name": "bold", "bids_modality": "fmap", "search_str": "_fmri_pa_T", "acq": "pa",
         "add_info": {**general_info, **sense_info, **rs_info, "PhaseEncodingDirection": "j"}},
        {"bids_name": "dwi", "bids_modality": "fmap", "search_str": "_dti_pa_T", "acq": "pa",
         "add_info": {**general_info, **sense_info, "PhaseEncodingDirection": "j"}},
        {"bids_name": "dwi", "bids_modality": "fmap", "search_str": "_dti_ap_T", "acq": "ap",
         "add_info": {**general_info, **sense_info, "PhaseEncodingDirection": "j-"}}
    ]

    #
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    info_file = oj(output_dir, "..", "info.txt")
    s = "\n%s" % dt.datetime.now()
    s += "\npublic_output: %s" % public_output
    s += "\nuse_new_ids: %s" % use_new_ids
    s += "\ninfo_list: %s" % info_list
    if not os.path.exists(info_file):
        with open(info_file, "w") as fi:
            fi.write(s)

    ds_desc_file = oj(output_dir, "dataset_description.json")
    if not os.path.exists(ds_desc_file):
        description = {"Name": "LHAB longitudinal healthy aging brain study",
                       "BIDSVersion": "1.0.0",
                       "License": "XXXXXX what license is this dataset distributed under? The use of license name "
                                  "abbreviations is suggested for specifying a license. A list of common licenses"
                                  " with suggested abbreviations can be found in appendix III.",
                       "Authors": "XXXXXX List of individuals who contributed to the creation/curation of the dataset",
                       "Acknowledgements": "XXXXXX who should be acknowledge in helping to collect the data",
                       "HowToAcknowledge": "XXXXXX Instructions how researchers using this dataset should "
                                           "acknowledge the original authors. This "
                                           "field can also be used to define a publication that should be cited in publications that use "
                                           "the dataset",
                       "Funding": "XXXXXX sources of funding (grant numbers)",
                       "DataSetVersion": args.ds_version}
        add_info_to_json(ds_desc_file, description, create_new=True)

    for old_subject_id in old_sub_id_list:
        submit_single_subject(old_subject_id,
                              ses_id_list,
                              raw_dir,
                              in_ses_folder,
                              output_dir,
                              info_list,
                              bvecs_from_scanner_file=bvecs_from_scanner_file,
                              public_output=public_output,
                              use_new_ids=use_new_ids,
                              new_id_lut_file=new_id_lut_file)

    print("\n\n\n\nDONE.\nConverted %d subjects." % len(old_sub_id_list))
    print(old_sub_id_list)

    # bids validator
    print("X" * 20 + "\nRuning BIDS validator")
    os.system("bids-validator %s" % output_dir)

    #
    print("X" * 20 + "\nTesting if correct files are there and others are correctly deleted...")

    shouldbe_there = [oj(output_dir, "dataset_description.json"),
                      oj(output_dir, "sub-lhabX9999/sub-lhabX9999_scans.tsv"),
                      oj(output_dir, "sub-lhabX9999/ses-tp1/anat/sub-lhabX9999_ses-tp1_run-1_T1w.nii.gz"),
                      oj(output_dir, "sub-lhabX9999/ses-tp3/anat/sub-lhabX9999_ses-tp3_run-1_T1w.nii.gz"),
                      oj(output_dir, "sub-lhabX9999/ses-tp1/anat/sub-lhabX9999_ses-tp1_run-1_T1w.json"),
                      oj(output_dir, "sub-lhabX9999/ses-tp3/anat/sub-lhabX9999_ses-tp3_run-1_T1w.json"),
                      oj(output_dir, "sub-lhabX9999/ses-tp1/anat/sub-lhabX9999_ses-tp1_acq-2D_run-1_FLAIR.nii.gz"),
                      oj(output_dir, "sub-lhabX9999/ses-tp1/anat/sub-lhabX9999_ses-tp1_acq-3D_run-1_FLAIR.nii.gz"),
                      oj(output_dir, "sub-lhabX9999/ses-tp3/func/sub-lhabX9999_ses-tp3_task-rest_run-1_bold.nii.gz"),
                      oj(output_dir, "sub-lhabX9999/ses-tp3/fmap/sub-lhabX9999_ses-tp3_acq-pa_run-1_bold.nii.gz"),
                      oj(output_dir, "sub-lhabX9999/ses-tp1/dwi/sub-lhabX9999_ses-tp1_acq-ap_run-1_dwi.nii.gz"),
                      oj(output_dir, "sub-lhabX9999/ses-tp1/dwi/sub-lhabX9999_ses-tp1_acq-ap_run-1_dwi.nii.gz"),
                      oj(output_dir, "sub-lhabX9999/ses-tp1/dwi/sub-lhabX9999_ses-tp1_acq-ap_run-1_dwi.nii.gz"),
                      oj(output_dir, "sub-lhabX9999/ses-tp1/dwi/sub-lhabX9999_ses-tp1_acq-ap_run-1_dwi.json"),
                      oj(output_dir, "sub-lhabX9999/ses-tp1/dwi/sub-lhabX9999_ses-tp1_acq-ap_run-1_dwi.bval"),
                      oj(output_dir, "sub-lhabX9999/ses-tp1/dwi/sub-lhabX9999_ses-tp1_acq-ap_run-1_dwi.bvec"),
                      oj(output_dir, "sub-lhabX9999/ses-tp3/fmap/sub-lhabX9999_ses-tp3_acq-ap_run-1_dwi.nii.gz"),
                      oj(output_dir, "sub-lhabX9999/ses-tp3/fmap/sub-lhabX9999_ses-tp3_acq-pa_run-1_dwi.nii.gz"),
                      ]

    for f in shouldbe_there:
        if not os.path.exists(f):
            raise FileNotFoundError("A file that the test should produce was missing: %s" % f)

    # check defacing is on
    f = oj(output_dir, "sub-lhabX9999/ses-tp1/anat/sub-lhabX9999_ses-tp1_run-1_T1w.json")
    with open(f) as fi:
        j = json.load(fi)
    if not j["Defaced"]:
        raise Exception("Defacing seems to be turned off. Exit. %s" % f)

    if public_output:
        shouldnotbe_there = [
            oj(output_dir, "sub-lhabX9999/ses-tp1/anat/sub-lhabX9999_ses-tp1_run-1_T1w.txt"),
            oj(output_dir, "sub-lhabX9999/par2nii_mapping.txt"),
        ]
        for f in shouldnotbe_there:
            if os.path.exists(f):
                raise FileExistsError("A file that the test should NOT produce was found: %s" % f)
    print("Everthing seems to be fine!")
