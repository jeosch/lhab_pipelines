import os
import glob
import pandas as pd
import argparse


def get_subject_duration(subject):
    """
    calculates the duration of each session
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="creates age, sex tables.")
    parser.add_argument('raw_dir', help='The directory with the RAW input dataset.'
                                        '\n original: bids_dir')
    parser.add_argument('output_base_dir', help='The directory where the output files '
                                                'should be stored.'
                                                '\n original: output_dir')
    parser.add_argument('--participant_file', help='participants that should be analyzed.'
                                                   'For the conversion wf this should be given as lhab_1234')
    parser.add_argument('--no-public_output',
                        help="Don't create public output.\nIf public_output: strips all info about original "
                             "subject_id, file, date \nDefault: use public_output",
                        default=True, dest="public_output", action='store_false')
    parser.add_argument('--no-use_new_ids', help="Don't use new subject ids. "
                                                 "\nDefault: Use new ids from mapping file",
                        default=True, dest="use_new_ids", action='store_false')
    parser.add_argument('--ds_version', help="Data set version (is added to output path)", default="dev")

    args = parser.parse_args()

    raw_dir = args.raw_dir

    # privacy settings
    public_output = args.public_output
    use_new_ids = args.use_new_ids
    if not (public_output and use_new_ids):
        private_str = "_PRIVATE"
    else:
        private_str = ""

    output_dir = os.path.join(args.output_base_dir, "LHAB_" + args.ds_version + private_str, "sourcedata")

    os.chdir(output_dir)
    subjects_list = glob.glob("sub*")
    print(output_dir)
    print(subjects_list)
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
