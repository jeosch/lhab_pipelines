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
import glob

from utils import get_new_ses_id, run_conversions


base_dir = "/data/"
raw_dir = os.path.join(base_dir, "raw")
output_dir = os.path.join(base_dir, "nifti")
ses_id_list = ["T1", "T2", "T3"]
in_ses_folder = "01_noIF"
bvecs_from_scanner_file = os.path.join(raw_dir, "00_bvecs/bvecs.fromscanner")

info_list = [
    # {"bids_name": "T1w", "bids_modality": "anat", "search_str": "_t1w_"},
    {"bids_name": "FLAIR", "bids_modality": "anat", "search_str": "_2dflair_"},
    {"bids_name": "dwi", "bids_modality": "dwi", "search_str": "_dti_T", "only_use_last": True},
    # {"bids_name": "bold", "bids_modality": "func", "search_str": "_fmri_T", "task": "rest"},
    # {"bids_name": "bold", "bids_modality": "fmap", "search_str": "_fmri_pa_T", "direction": "ap"},
    # {"bids_name": "dwi", "bids_modality": "fmap", "search_str": "_dti_pa_T", "direction": "pa"},
    # {"bids_name": "dwi", "bids_modality": "fmap", "search_str": "_dti_ap_T", "direction": "ap"}
]



#
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# get subject list
raw_subjects_list = []
for ses in ses_id_list:
    search_dir = os.path.join(raw_dir, ses, in_ses_folder)
    os.chdir(search_dir)
    raw_subjects_list += glob.glob("lhab*")
old_subject_id_list = list(set([s[:9] for s in raw_subjects_list]))

for old_ses_id in ses_id_list:
    new_ses_id = get_new_ses_id(old_ses_id)

    for old_subject_id in old_subject_id_list:
        subject_ses_folder = os.path.join(raw_dir, old_ses_id, in_ses_folder)
        os.chdir(subject_ses_folder)
        subject_folder = glob.glob(old_subject_id + "*")
        assert len(subject_folder) < 2, "more than one subject folder %s" % old_subject_id

        if subject_folder:
            subject_folder = subject_folder[0]
            abs_subject_folder = os.path.abspath(subject_folder)
            os.chdir(subject_folder)
            run_conversions(old_subject_id, old_ses_id, abs_subject_folder, output_dir, info_list, bvecs_from_scanner_file)
