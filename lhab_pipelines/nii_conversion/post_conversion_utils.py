import os
from glob import glob
import pandas as pd

from lhab_pipelines.nii_conversion.utils import get_public_sub_id, get_private_sub_id, get_clean_subject_id, \
    get_clean_ses_id, fetch_demos
from lhab_pipelines.utils import read_protected_file, to_tsv, read_tsv
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
    subjects_list = glob("sub*")
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


def compare_par_nii(output_dir, old_sub_id_list, raw_dir, ses_id_list, in_ses_folder, info_list, new_id_lut_file):
    """
    - Checks that all subjects from subject list are in sourcedata
    - Checks that par and nii filecount agrees
    - Exports nii filecount to output_dir
    """
    # first check that all subjects from id list are in the output_dir
    print("\nchecking that all subjects from id list are in the output_dir...")
    layout = BIDSLayout(output_dir)
    subjects_list = layout.get_subjects()

    for old_sub_id in old_sub_id_list:
        new_sub_id = get_public_sub_id(old_sub_id, new_id_lut_file)
        sub_dir = os.path.join(output_dir, "sub-" + new_sub_id)
        f = glob(sub_dir)
        if not f:
            raise Exception("No folder not found: %s" % sub_dir)
    print("%d subjects from list found in folder %s. Seems OK...\n" % (len(old_sub_id_list), output_dir))

    # compare filecount of par and nii files and export
    filecount = pd.DataFrame([])
    for new_sub_id in subjects_list:
        old_sub_id = get_private_sub_id(new_sub_id, new_id_lut_file)

        for old_ses_id in ses_id_list:
            new_ses_id = "tp" + old_ses_id[-1]
            sub_ses_par_dir = os.path.join(raw_dir, old_ses_id, in_ses_folder,
                                           old_sub_id + "_t%s_raw" % new_ses_id[-1])
            sub_ses_nii_dir = os.path.join(output_dir, "sub-" + new_sub_id, "ses-" + new_ses_id)

            n_files = OrderedDict([("subject_id", new_sub_id), ("session_id", new_ses_id)])

            for info in info_list:
                par_search_str = os.path.join(sub_ses_par_dir, "*" + info["search_str"] + "*.par")
                par_f = glob(par_search_str)
                n_files_par = len(par_f)

                if "acq" in info.keys():
                    acq_str = "_acq-" + info["acq"]
                else:
                    acq_str = ""
                if "direction" in info.keys():
                    dir_str = "_dir-" + info["direction"]
                else:
                    dir_str = ""
                nii_search_str = os.path.join(sub_ses_nii_dir, info["bids_modality"], "*" + acq_str + "*" + dir_str
                                              + "*" + info["bids_name"] + "*.nii.gz")
                nii_f = glob(nii_search_str)
                n_files_nifti = len(nii_f)

                c = info["bids_modality"] + "_" + info["bids_name"] + \
                    acq_str.replace("-", "") + dir_str.replace("-", "")

                n_files[c] = [n_files_nifti]

                if not n_files_par == n_files_nifti:
                    raise Exception("missmatch between par and nii file count %s %s %s %s" % (new_sub_id, new_ses_id,
                                                                                              par_search_str,
                                                                                              nii_search_str))
                # TODO check physio
                if "physio" in info.keys() and info["physio"]:
                    phys_par_search_str = os.path.join(sub_ses_par_dir, "*" + info["search_str"] + "*_physio.log")
                    phys_par_f = glob(phys_par_search_str)
                    phys_n_files_par = len(phys_par_f)

                    phys_nii_search_str = os.path.join(sub_ses_nii_dir, info["bids_modality"], "*" + acq_str + "*" +
                                                       dir_str + "*" + info["bids_name"] + "*_physio.tsv")
                    phys_nii_f = glob(phys_nii_search_str)
                    phys_n_files_nifti = len(phys_nii_f)

                    c = info["bids_modality"] + "_" + info["bids_name"] + \
                        acq_str.replace("-", "") + dir_str.replace("-", "") + "_physio"
                    n_files[c] = [phys_n_files_nifti]

            filecount = filecount.append(pd.DataFrame(n_files))

    output_file = os.path.join(output_dir, "n_files.tsv")
    to_tsv(filecount, output_file)
    print("Compared filecount from par and nifti files. Seems OK...")
    print("Filecount written to %s" % output_file)


def reduce_sub_files(bids_dir, output_file, sub_file):
    df = pd.DataFrame([])
    layout = BIDSLayout(bids_dir)
    files = layout.get(extensions=sub_file)
    for file in [f.filename for f in files]:
        print(file)
        df_ = read_tsv(file)
        df = pd.concat((df, df_))

    to_tsv(df, os.path.join(bids_dir, output_file))