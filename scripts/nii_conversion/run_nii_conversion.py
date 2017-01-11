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

"""
import os, argparse
from lhab_pipelines.utils import read_tsv, add_info_to_json
from lhab_pipelines.nii_conversion.conversion import submit_single_subject
import datetime as dt
import numpy as np

# TODO remove sub_id from subject list files

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

    args = parser.parse_args()

    raw_dir = args.raw_dir

    # privacy settings
    public_output = args.public_output
    use_new_ids = args.use_new_ids

    # base_dir = "/data/"
    # raw_dir = os.path.join(base_dir, "raw")
    face_dir = os.path.join(raw_dir, "00_face")
    output_dir = os.path.join(args.output_base_dir, "nifti", "sourcedata")

    ###
    if args.participant_label:
        old_sub_id_list = [s.strip() for s in args.participant_label]
        exclude_sub_id_list = "none"
    else:
        # SUBJECT ID STUFF
        all_sub_file = os.path.join(raw_dir, "00_PRIVATE_sub_lists/lhab_all_subjects.tsv")
        exclude_sub_file = None  # os.path.join(raw_dir,
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
        {"bids_name": "FLAIR", "bids_modality": "anat", "search_str": "_2dflair_", "acq": "2D", "deface": True,
         "add_info": {**general_info}},
        {"bids_name": "FLAIR", "bids_modality": "anat", "search_str": "_3dflair_", "acq": "3D", "deface": True,
         "add_info": {**general_info}},

        # dwi
        {"bids_name": "dwi", "bids_modality": "dwi", "search_str": "_dti_T", "only_use_last": True, "direction": "ap",
         "add_info": {**general_info, **sense_info, "PhaseEncodingDirection": "j-"}},

        # func
        {"bids_name": "bold", "bids_modality": "func", "search_str": "_fmri_T", "task": "rest", "physio": True,
         "add_info": {**general_info, **sense_info, **rs_info, "PhaseEncodingDirection": "j-"}},

        # fieldmaps
        {"bids_name": "bold", "bids_modality": "fmap", "search_str": "_fmri_pa_T", "direction": "pa",
         "add_info": {**general_info, **sense_info, **rs_info, "PhaseEncodingDirection": "j"}},
        {"bids_name": "dwi", "bids_modality": "fmap", "search_str": "_dti_pa_T", "direction": "pa",
         "add_info": {**general_info, **sense_info, "PhaseEncodingDirection": "j"}},
        {"bids_name": "dwi", "bids_modality": "fmap", "search_str": "_dti_ap_T", "direction": "ap",
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
                       "BIDSVersion": "1.0.0"}
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
                              face_dir=face_dir,
                              new_id_lut_file=new_id_lut_file)

    print("\n\n\n\nDONE.\nConverted %d subjects." % len(old_sub_id_list))
    print(old_sub_id_list)
