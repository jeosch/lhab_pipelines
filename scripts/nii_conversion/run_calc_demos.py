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

if __name__ == "__main__":

    # privacy settings
    public_output = True
    use_new_ids = True

    base_dir = "/data/"
    raw_dir = os.path.join(base_dir, "raw")
    face_dir = os.path.join(raw_dir, "00_face")
    output_dir = os.path.join(base_dir, "nifti", "sourcedata")

    ses_id_list = ["T1", "T2", "T3", "T4", "T5"]
    in_ses_folder = "01_noIF"
    bvecs_from_scanner_file = os.path.join(raw_dir, "00_bvecs/bvecs.fromscanner")
    all_sub_file = os.path.join(raw_dir, "00_PRIVATE_sub_lists/lhab_all_subjects.tsv")
    exclude_sub_file = os.path.join(raw_dir, "00_PRIVATE_sub_lists/strange_tp5_sub_exclude.tsv")
    new_id_lut_file = os.path.join(raw_dir, "00_PRIVATE_sub_lists/new_sub_id_lut.tsv")
    demo_file = os.path.join(raw_dir, "00_PRIVATE_sub_lists/dob.zip")


    #
    pwd = getpass.getpass("Enter the Password for dob file:")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # get subject and exclude subj list
    old_sub_id_list = read_tsv(all_sub_file)["sub_id"].tolist()

    try:
        exclude_sub_id_list = read_tsv(exclude_sub_file)["sub_id"].tolist()
        for bad in exclude_sub_id_list:
            old_sub_id_list.remove(bad)
            print("Removed %s" % bad)
    except:
        exclude_sub_id_list = "none"

    # convert_subjects(old_sub_id_list,
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
    if exclude_sub_file:
        print("\n\nDid not convert the following subjects: %s "
              "\nbecause they were in the exclude subjects list %s" % (exclude_sub_id_list, exclude_sub_file))
