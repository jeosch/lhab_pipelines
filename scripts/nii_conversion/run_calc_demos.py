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
import argparse
import getpass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="creates age, sex tables.")
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
        old_sub_id_list = read_tsv(args.participant_file)["sub_id"].tolist()
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

    calc_demos(old_sub_id_list,
               ses_id_list,
               raw_dir,
               in_ses_folder,
               output_dir,
               demo_file,
               pwd,
               use_new_ids=use_new_ids,
               new_id_lut_file=new_id_lut_file,
               public_output=public_output,
               )

    print("\n\n\n\nDONE.\nConverted %d subjects." % len(old_sub_id_list))
    print(old_sub_id_list)
