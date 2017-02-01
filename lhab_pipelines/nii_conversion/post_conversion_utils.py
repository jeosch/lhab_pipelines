import glob
import os
from glob import glob

import pandas as pd

from lhab_pipelines.nii_conversion.utils import get_public_sub_id, get_new_subject_id, get_new_ses_id, fetch_demos
from lhab_pipelines.utils import read_protected_file, to_tsv


def get_subject_duration(subject):
    """
    calculates the duration of each session by checking the <subject>_scans.tsv file
    """
    scans_file = os.path.join(subject, subject + "_scans.tsv")
    df = pd.read_csv(scans_file, sep="\t", parse_dates=["acq_time"])
    g = df.groupby("session_id")

    duration = pd.DataFrame(
        {"duration_minutes": g["acq_time"].apply(lambda x: x.max() - x.min()).dt.total_seconds() / 60.})
    duration["subject_id"] = subject
    duration["session_id"] = duration.index
    duration.set_index("subject_id", inplace=True, drop=True)
    return duration


def calc_session_duration(output_base_dir, ds_version, public_output, use_new_ids):
    """
    looks for subjects in output_dir and checks session durations
    raises Exception if duration is longer 2h
    """
    # privacy settings
    if not (public_output and use_new_ids):
        private_str = "_PRIVATE"
    else:
        raise Exception("cannot calc session duration from non private data.")

    output_dir = os.path.join(output_base_dir, "LHAB_" + ds_version + private_str, "sourcedata")

    os.chdir(output_dir)
    subjects_list = glob.glob("sub*")
    if not subjects_list:
        raise Exception("No subjects found in %s" % output_dir)

    df = pd.DataFrame([])
    for subject in subjects_list:
        subject_duration = get_subject_duration(subject)
        df = df.append(subject_duration)

    out_file = os.path.join(output_dir, "session_duration.tsv")
    print(out_file)
    df.to_csv(out_file, sep="\t")

    if df["duration_minutes"].max() > 120:
        raise Exception("something with the data is probably off. max duration of %s" % df["duration_minutes"].max())


def calc_demos(old_sub_id_list,
               ses_id_list,
               raw_dir,
               in_ses_folder,
               output_dir,
               demo_file,
               pwd,
               use_new_ids=True,
               new_id_lut_file=None,
               public_output=True,
               ):
    '''
    use_new_ids: if True, uses new id from mapping file
    '''
    assert pwd != "", "password empty"
    demo_df = read_protected_file(demo_file, pwd, "demos.txt")

    out_demo_df = pd.DataFrame([])
    out_acq_time_df = pd.DataFrame([])
    for old_subject_id in old_sub_id_list:
        for old_ses_id in ses_id_list:
            subject_ses_folder = os.path.join(raw_dir, old_ses_id, in_ses_folder)
            os.chdir(subject_ses_folder)
            subject_folder = sorted(glob(old_subject_id + "*"))
            assert len(subject_folder) < 2, "more than one subject folder %s" % old_subject_id

            if subject_folder:
                subject_folder = subject_folder[0]
                abs_subject_folder = os.path.abspath(subject_folder)
                os.chdir(abs_subject_folder)

                if use_new_ids:
                    bids_sub = "sub-" + get_public_sub_id(old_subject_id, new_id_lut_file)
                else:
                    bids_sub = "sub-" + get_new_subject_id(old_subject_id)
                bids_ses = "ses-" + get_new_ses_id(old_ses_id)

                par_file_list = glob(os.path.join(abs_subject_folder, "*.par"))

                if par_file_list:
                    par_file = par_file_list[0]
                    df_subject, df_acq_time_subject = fetch_demos(demo_df, old_subject_id, bids_sub, bids_ses,
                                                                  par_file)
                    out_demo_df = pd.concat((out_demo_df, df_subject))
                    out_acq_time_df = pd.concat((out_acq_time_df, df_acq_time_subject))

    to_tsv(out_demo_df, os.path.join(output_dir, "participants.tsv"))
    if not public_output:
        to_tsv(out_acq_time_df, os.path.join(output_dir, "acq_time.tsv"))