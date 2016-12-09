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

TODO:
-fmaps
-slice timing

"""
import os
from lhab_pipelines.utils import read_tsv
from lhab_pipelines.nii_conversion.conversion import convert_subjects

if __name__ == "__main__":

    n_jobs = -1

    # privacy settings
    public_output = True
    use_new_ids = True

    base_dir = "/data/"
    raw_dir = os.path.join(base_dir, "raw")
    face_dir = os.path.join(raw_dir, "00_face")
    output_dir = os.path.join(base_dir, "nifti", "sourcedata")

    ses_id_list = ["T1", "T2", "T3"]
    in_ses_folder = "01_noIF"
    bvecs_from_scanner_file = os.path.join(raw_dir, "00_bvecs/bvecs.fromscanner")
    all_sub_file = os.path.join(raw_dir, "00_PRIVATE_sub_lists/lhab_all_subjects.tsv")
    exclude_sub_file = os.path.join(raw_dir, "00_PRIVATE_sub_lists/tp5_sub_exclude.tsv")
    new_id_lut_file = os.path.join(raw_dir, "00_PRIVATE_sub_lists/new_sub_id_lut.tsv")

    info_list = [
        {"bids_name": "T1w", "bids_modality": "anat", "search_str": "_t1w_", "deface": False},
        # {"bids_name": "FLAIR", "bids_modality": "anat", "search_str": "_2dflair_"},
        # {"bids_name": "dwi", "bids_modality": "dwi", "search_str": "_dti_T", "only_use_last": True},
        # {"bids_name": "bold", "bids_modality": "func", "search_str": "_fmri_T", "task": "rest"},
        # {"bids_name": "bold", "bids_modality": "fmap", "search_str": "_fmri_pa_T", "direction": "ap"},
        # {"bids_name": "dwi", "bids_modality": "fmap", "search_str": "_dti_pa_T", "direction": "pa"},
        # {"bids_name": "dwi", "bids_modality": "fmap", "search_str": "_dti_ap_T", "direction": "ap"}
    ]

    #
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # get subject and exclude subj list
    old_sub_id_list = read_tsv(all_sub_file)["sub_id"].tolist()

    try:
        exclude_sub_id_list = read_tsv(exclude_sub_file)["sub_id"].tolist()
    except:
        pass
    for bad in exclude_sub_id_list:
        print(bad)
        old_sub_id_list.remove(bad)
        print("Removed %s" % bad)

    convert_subjects(old_sub_id_list,
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
                     n_jobs=n_jobs)

    print("\n\n\n\nDONE.\nConverted %d subjects." % len(old_sub_id_list))
    print("Did not convert the following subjects: %s "
          "\nbecause they were in the exclude subjects list %s" % (exclude_sub_id_list, exclude_sub_file))
