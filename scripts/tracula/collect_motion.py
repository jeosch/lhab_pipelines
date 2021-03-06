import pandas as pd
import os
from glob import glob

root_path = "/Volumes/lhab_secure/02_LHAB/00_Data/4Franz/tracula/tracula_out_data/tracula_out_data/"
out_path = "/Volumes/lhab_secure/02_LHAB/00_Data/4Franz/tracula/motion"

if not os.path.exists(out_path):
    os.mkdir(out_path)

df = pd.DataFrame([])

os.chdir(root_path)
subject_dirs = glob("run_sub-*")
subject_labels = [s.split("-")[-1] for s in subject_dirs]

for sub in subject_labels:
    session_dirs = glob(os.path.join(root_path, "run_sub-{subject_label}/output/sub-{"
                                                "subject_label}_ses-tp*.long.sub-{subject_label}.base".format(
        subject_label=sub)))
    session_labels = [os.path.basename(sd).split("-")[-2].split(".")[0] for sd in session_dirs]
    for ses in session_labels:
        dwi_file = os.path.join(root_path, "run_sub-{subject_label}/output/sub-{subject_label}_ses-{"
                                           "ses_label}.long.sub-{subject_label}.base/dmri/dwi_motion.txt".format(
            subject_label=sub,
            ses_label=ses))
        print(dwi_file)
        df_ = pd.read_csv(dwi_file, sep=" ")
        df_.index = [sub]
        df_["in_file"] = dwi_file
        df_["session"] = ses
        df = df.append(df_)


# calculate mean motion based on standardized motion measures
# inspired by Yendiki, A., Koldewyn, K., Kakunoori, S., Kanwisher, N., & Fischl, B. (2013).
# http://doi.org/10.1016/j.neuroimage.2013.11.027
# since 'PercentBadSlices' and 'AvgDropoutScore' show little variance, we only consider motion
for m in ['AvgTranslation', 'AvgRotation']:
        ql, med, qu = df[m].quantile(q=[.25,.5,.75])
        df["std_" + m] = (df[m] - med) / (qu - ql)
df["AvgMotion"] = df[['std_AvgTranslation', 'std_AvgRotation']].mean(1)


df.to_csv(os.path.join(out_path, "tracula_motion.txt"), sep="\t")
