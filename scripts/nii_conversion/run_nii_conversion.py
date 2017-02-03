"""

|-- T1
|   `-- 01_noIF
|       `-- lhab_xxxx_t1_raw
|           |-- lhab_xxxx_2dflair_T1.par
|           |-- lhab_xxxx_2dflair_T1.rec
...
|-- T2
|   `-- 01_noIF
|       `-- lhab_xxxx_t2_raw
|           |-- lhab_xxxx_2dflair_T2.par
|           |-- lhab_xxxx_2dflair_T2.rec
...

# only converts flair if private output due to unreliable defacing
"""
import os, argparse
from lhab_pipelines.utils import read_tsv, add_info_to_json
from lhab_pipelines.nii_conversion.conversion import submit_single_subject
import datetime as dt
import numpy as np

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

    output_dir = os.path.join(args.output_base_dir, "LHAB_" + args.ds_version + private_str, "sourcedata")

    ###
    if args.participant_label:
        old_sub_id_list = [s.strip() for s in args.participant_label]
        exclude_sub_id_list = "none"
    else:
        # SUBJECT ID STUFF
        all_sub_file = os.path.join(raw_dir, "00_PRIVATE_sub_lists/lhab_all_subjects.tsv")
        old_sub_id_list = read_tsv(all_sub_file)["subject_id"].tolist()

    ###
    ###
    ses_id_list = ["T1", "T2", "T3", "T4", "T5"]
    in_ses_folder = "01_noIF"
    bvecs_from_scanner_file = os.path.join(raw_dir, "00_bvecs/bvecs.fromscanner")
    new_id_lut_file = os.path.join(raw_dir, "00_PRIVATE_sub_lists/new_sub_id_lut.tsv")

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

    info_file = os.path.join(output_dir, "..", "info.txt")
    s = "\n%s" % dt.datetime.now()
    s += "\npublic_output: %s" % public_output
    s += "\nuse_new_ids: %s" % use_new_ids
    s += "\ninfo_list: %s" % info_list
    if not os.path.exists(info_file):
        with open(info_file, "w") as fi:
            fi.write(s)

    ds_desc_file = os.path.join(output_dir, "dataset_description.json")
    if not os.path.exists(ds_desc_file):
        description = {"Name": "LHAB longitudinal healthy aging brain study",
                       "BIDSVersion": "1.0.0",
                       # "License": "XXXXXX what license is this dataset distributed under? The use of license name "
                       #            "abbreviations is suggested for specifying a license. A list of common licenses"
                       #            " with suggested abbreviations can be found in appendix III.",
                       # "Authors": "XXXXXX List of individuals who contributed to the creation/curation of the dataset",
                       # "Acknowledgements": "XXXXXX who should be acknowledge in helping to collect the data",
                       # "HowToAcknowledge": "XXXXXX Instructions how researchers using this dataset should "
                       #                     "acknowledge the original authors. This "
                       #                     "field can also be used to define a publication that should be cited in publications that use "
                       #                     "the dataset",
                       "Funding": "Velux Stiftung (project No. 369)",
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
