
import os
import glob
import pandas as pd


def get_subject_duration(subject):
    """
    calculates the duration of each session
    """
    scans_file = os.path.join(subject, subject + "_scans.tsv")
    df = pd.read_csv(scans_file, sep="\t", parse_dates=["acq_time"])
    g = df.groupby("ses_id")

    duration = pd.DataFrame({"duration_minutes": g["acq_time"].apply(lambda x: x.max()-x.min()).dt.total_seconds() / 60.})
    duration["sub_id"] = subject
    duration["ses_id"] = duration.index
    duration.set_index("sub_id", inplace=True, drop=True)
    return duration



base_dir = "/data/nifti"


os.chdir(base_dir)
subjects_list = glob.glob("sub*")

df = pd.DataFrame([])

for subject in subjects_list:
    subject_duration = get_subject_duration(subject)
    df = df.append(subject_duration)

