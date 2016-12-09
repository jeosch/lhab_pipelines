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
n_jobs = -1

import os
import glob
from joblib import Parallel, delayed

from lhab_pipelines.nii_conversion.conversion import run_conversions
from lhab_pipelines.utils import read_tsv

base_dir = "/data/"
raw_dir = os.path.join(base_dir, "raw")
output_dir = os.path.join(base_dir, "nifti")
face_dir = os.path.join(raw_dir, "00_face")

ses_id_list = ["T1", "T2", "T3"]
in_ses_folder = "01_noIF"
bvecs_from_scanner_file = os.path.join(raw_dir, "00_bvecs/bvecs.fromscanner")
all_sub_file= os.path.join(raw_dir, "00_PRIVATE_sub_lists/lhab_all_subjects.tsv")
new_id_lut_file= os.path.join(raw_dir, "00_PRIVATE_sub_lists/new_sub_id_lut.tsv")


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

# get subject list
old_subject_id_list = read_tsv(all_sub_file)["sub_id"].tolist()


def submit_subject(old_subject_id):
    for old_ses_id in ses_id_list:
        subject_ses_folder = os.path.join(raw_dir, old_ses_id, in_ses_folder)
        os.chdir(subject_ses_folder)
        subject_folder = sorted(glob.glob(old_subject_id + "*"))
        assert len(subject_folder) < 2, "more than one subject folder %s" % old_subject_id

        if subject_folder:
            subject_folder = subject_folder[0]
            abs_subject_folder = os.path.abspath(subject_folder)
            os.chdir(subject_folder)
            run_conversions(old_subject_id, old_ses_id, abs_subject_folder, output_dir, info_list,
                            bvecs_from_scanner_file=bvecs_from_scanner_file,
                            public_output=True,
                            face_dir=face_dir,
                            new_id_lut_file=new_id_lut_file)


Parallel(n_jobs=n_jobs)(delayed(submit_subject)(old_subject_id) for old_subject_id in old_subject_id_list)
