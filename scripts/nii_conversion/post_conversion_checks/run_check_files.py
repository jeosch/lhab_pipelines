# import pandas as pd
# def read_tsv(filename):
#     return pd.read_csv(filename, sep="\t")
#
# df=read_tsv("checks/n_files.tsv")
#
# g = df.groupby("sub_id")
# n_dwis = g.sum()
# df=df.set_index(df.sub_id)
# df_o=df[["ses_id", "dwi"]].pivot(columns="ses_id")
# df_o.to_excel("/Users/franzliem/Desktop/lhab_dwi_missing.xlsx")


import os
import glob
import pandas as pd
from lhab_pipelines.nii_conversion.utils import get_json
from lhab_pipelines.utils import to_tsv, get_json

orig_path = os.getcwd()
base_dir = "/data/"


raw_dir = os.path.join(base_dir, "raw")
nifti_dir = os.path.join(base_dir, "nifti")
out_dir = os.path.join(base_dir, "checks")

ses_id_list = ["T1", "T2", "T3"]
in_ses_folder = "01_noIF"

info_list = [
    # {"seq_name": "T1w", "bids_modality": "anat", "search_str": "T1w"},
    # {"seq_name": "FLAIR", "bids_modality": "anat", "search_str": "FLAIR"},
    {"seq_name": "dwi", "bids_modality": "dwi", "search_str": "dwi"},
    # {"seq_name": "bold", "bids_modality": "func", "search_str": "bold"},
    # {"seq_name": "fmap_bold", "bids_modality": "fmap", "search_str": "bold"},
    # {"seq_name": "fmap_dwi", "bids_modality": "fmap", "search_str": "dwi"},
]


# get subject list
os.chdir(nifti_dir)
subjects_list = glob.glob("sub-lhab*")

df = pd.DataFrame([])
scan_duration = pd.DataFrame([])

for sub_id in subjects_list:
    os.chdir(os.path.join(nifti_dir, sub_id))
    ses_id_list = glob.glob("ses-*")

    for ses_id in ses_id_list:
        n_files = {"sub_id": sub_id, "ses_id": ses_id}

        sub_ses_path = os.path.join(nifti_dir, sub_id, ses_id)
        for seq in info_list:
            sub_ses_mod_path = os.path.join(sub_ses_path, seq["bids_modality"])
            if os.path.exists(sub_ses_mod_path):
                os.chdir(sub_ses_mod_path)
                file_list = glob.glob("*" + seq["search_str"] + "*.nii.gz")
                n_files[seq["seq_name"]] = [len(file_list)]

                if seq["seq_name"] == "bold":
                    for f in file_list:
                        json_file = f.strip(".nii.gz") + ".json"
                        bids_data = get_json(json_file)
                        bold_info = pd.DataFrame({"subject_id": sub_id, "sesssion_id": ses_id, "filename": [json_file],
                                     "scan_duration": [bids_data["ScanDurationSec"]]})
                        scan_duration = scan_duration.append(bold_info)

            else:
                n_files[seq["seq_name"]] = 0

        df = df.append(pd.DataFrame(n_files))  # , ignore_index=True)

df = df[["subject_id", "sesssion_id", "dwi" ]]#"T1w", "bold", "dwi", "fmap_bold", "fmap_dwi", "FLAIR"]]

if not os.path.exists(out_dir):
    os.makedirs(out_dir)
to_tsv(df, os.path.join(out_dir, "n_files.tsv"))
to_tsv(scan_duration, os.path.join(out_dir, "rest_scan_duration.tsv"))
os.chdir(orig_path)
