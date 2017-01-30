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
import os
from lhab_pipelines.utils import read_tsv
from lhab_pipelines.nii_conversion.conversion import calc_demos
import getpass
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="creates age, sex tables.")
    parser.add_argument('raw_dir', help='The directory with the RAW input dataset.'
                                        '\n original: bids_dir')
    parser.add_argument('output_base_dir', help='The directory where the output files '
                                                'should be stored.'
                                                '\n original: output_dir')
    parser.add_argument('analysis_level', help='Level of the analysis that will be performed. ',
                        choices=['group'])
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
    parser.add_argument('--pw', help="pw",)
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
    else:
        raise Exception("No subjects specified")
    # exclude_sub_id_list = "none"
    # else:
    #     # SUBJECT ID STUFF
    #     all_sub_file = os.path.join(raw_dir, "00_PRIVATE_sub_lists/lhab_all_subjects.tsv")
    #     exclude_sub_file = None  # os.path.join(raw_dir,
    #     # "00_PRIVATE_sub_lists/tp5_sub_exclude.tsv")
    #
    #     # get subject and exclude subj list
    #     old_sub_id_list = read_tsv(all_sub_file)["sub_id"].tolist()
    #
    #     try:
    #         exclude_sub_id_list = read_tsv(exclude_sub_file)["sub_id"].tolist()
    #         for bad in exclude_sub_id_list:
    #             old_sub_id_list.remove(bad)
    #             print("Removed %s" % bad)
    #     except:
    #         exclude_sub_id_list = "none"

    ses_id_list = ["T1", "T2", "T3", "T4", "T5"]
    in_ses_folder = "01_noIF"
    new_id_lut_file = os.path.join(raw_dir, "00_PRIVATE_sub_lists/new_sub_id_lut.tsv")
    demo_file = os.path.join(raw_dir, "00_PRIVATE_sub_lists/dob.zip")

    #
    pwd = args.pw #getpass.getpass("Enter the Password for dob file:")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

        # # get subject and exclude subj list
        # old_sub_id_list = read_tsv(all_sub_file)["sub_id"].tolist()
        #
        # try:
        #     exclude_sub_id_list = read_tsv(exclude_sub_file)["sub_id"].tolist()
        #     for bad in exclude_sub_id_list:
        #         old_sub_id_list.remove(bad)
        #         print("Removed %s" % bad)
        # except:
        exclude_sub_id_list = "none"

    calc_demos(old_sub_id_list,
               ses_id_list,
               raw_dir,
               in_ses_folder,
               output_dir,
               demo_file,
               pwd,
               use_new_ids=use_new_ids,
               new_id_lut_file=new_id_lut_file,
               )

    print("\n\n\n\nDONE.\nConverted %d subjects." % len(old_sub_id_list))
    print(old_sub_id_list)
