"checks if n files in raw and converted folder are the same"
import os
from glob import glob
from lhab_pipelines.nii_conversion.utils import get_public_sub_id

orig_path = os.getcwd()
base_dir = "/data/"

raw_dir = os.path.join(base_dir, "raw")
nifti_dir = os.path.join(base_dir, "nifti", "sourcedata")
# out_dir = os.path.join(base_dir, "checks")
new_id_lut_file = os.path.join(raw_dir, "00_PRIVATE_sub_lists/new_sub_id_lut.tsv")

ses_id_list = ["T1", "T2", "T3", "T4", "T5"]
in_ses_folder = "01_noIF"

info_list = [
    {"bids_name": "T1w", "bids_modality": "anat", "search_str": "_t1w_", "deface": True},
    # {"bids_name": "FLAIR", "bids_modality": "anat", "search_str": "_2dflair_"},
    # {"bids_name": "dwi", "bids_modality": "dwi", "search_str": "_dti_T", "only_use_last": True},
    # {"bids_name": "bold", "bids_modality": "func", "search_str": "_fmri_T", "task": "rest"},
    # {"bids_name": "bold", "bids_modality": "fmap", "search_str": "_fmri_pa_T", "direction": "ap"},
    # {"bids_name": "dwi", "bids_modality": "fmap", "search_str": "_dti_pa_T", "direction": "pa"},
    # {"bids_name": "dwi", "bids_modality": "fmap", "search_str": "_dti_ap_T", "direction": "ap"}
]

#
bad = []

for old_ses_id in ses_id_list:
    new_ses_id = "tp" + old_ses_id[-1]
    os.chdir(os.path.join(raw_dir, old_ses_id, in_ses_folder))
    old_subject_list = ["_".join(s.split("_")[:2]) for s in glob("lhab*")]

    for old_sub_id in old_subject_list:
        new_sub_id = get_public_sub_id(old_sub_id, new_id_lut_file)
        print(new_sub_id, new_ses_id)
        for info in info_list:
            search_str = os.path.join(raw_dir, old_ses_id, in_ses_folder, old_sub_id + "_t%s_raw" % new_ses_id[-1],
                                      "*" + info["search_str"] + "*.par")
            f = glob(search_str)
            n_files_raw = len(f)

            search_str = os.path.join(nifti_dir, "sub-" + new_sub_id, "ses-" + new_ses_id, info["bids_modality"],
                                      "*" + info["bids_name"] + "*.nii.gz")
            n_files_nifti = len(glob(search_str))
            if not n_files_raw == n_files_nifti:
                bad.append([old_sub_id, new_sub_id, new_ses_id, n_files_raw, n_files_nifti])


print("XXXXXXX\n bad subj\n")
print(bad)

