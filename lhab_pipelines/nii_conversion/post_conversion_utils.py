import glob
import os
from glob import glob

import pandas as pd

from lhab_pipelines.nii_conversion.utils import get_public_sub_id, get_private_sub_id, get_clean_subject_id, \
    get_clean_ses_id, fetch_demos
from lhab_pipelines.utils import read_protected_file, to_tsv
from bids.grabbids import BIDSLayout
from collections import OrderedDict


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


def calc_session_duration(output_dir, public_output, use_new_ids):
    """
    looks for subjects in output_dir and checks session durations
    raises Exception if duration is longer 2h
    """
    # privacy settings
    if public_output and use_new_ids:
        raise Exception("cannot calc session duration from non private data.")

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


def calc_demos(output_dir,
               ses_id_list,
               raw_dir,
               in_ses_folder,
               demo_file,
               pwd,
               use_new_ids=True,
               new_id_lut_file=None,
               public_output=True,
               ):
    '''
    Calcluates demos from acq_time
    '''
    assert pwd != "", "password empty"
    demo_df = read_protected_file(demo_file, pwd, "demos.txt")

    out_demo_df = pd.DataFrame([])
    out_acq_time_df = pd.DataFrame([])

    layout = BIDSLayout(output_dir)
    new_sub_id_list = layout.get_subjects()

    for new_subject_id in new_sub_id_list:
        old_subject_id = get_private_sub_id(new_subject_id, new_id_lut_file)

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
                    bids_sub = new_subject_id
                else:
                    bids_sub = get_clean_subject_id(old_subject_id)
                bids_ses = get_clean_ses_id(old_ses_id)

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

    print("\n\n\n\nDONE.\nExported demos for %d subjects." % len(new_sub_id_list))
    print(new_sub_id_list)


def get_scan_duration(output_dir, modality="func", task="rest"):
    """

    """
    layout = BIDSLayout(output_dir)
    subjects_list = layout.get_subjects()

    scan_duration = pd.DataFrame([])

    #
    for sub_id in subjects_list:
        sub_dir = os.path.join(output_dir, "sub-" + sub_id)
        ses_id_list = layout.get_sessions(subject=sub_id)

        for ses_id in ses_id_list:
            sub_ses_path = os.path.join(sub_dir, "ses-" + ses_id)
            f = layout.get(subject=sub_id, session=ses_id, modality=modality, task=task, extensions='.nii.gz')
            if len(f) > 1:
                raise Exception("something went wrong, more than one %s %s file detected: %s" % (modality, task, f))
            elif len(f) == 1:
                duration = (layout.get_metadata(f[0].filename)["ScanDurationSec"])
                scan_duration_sub = pd.DataFrame(OrderedDict([("subject_id", sub_id), ("sesssion_id", ses_id),
                                                              ("scan_duration_s", [duration])]))
                scan_duration = scan_duration.append(scan_duration_sub)

    out_str = modality
    if task:
        out_str += "_" + task
    output_file = os.path.join(output_dir, "scan_duration_%s.tsv" % out_str)
    print("Writing scan duration to %s" % output_file)
    to_tsv(scan_duration, output_file)
