import os
from glob import glob
import pandas as pd
import shutil

root_path = "/Volumes/lhab_secure/02_LHAB/00_Data/00_MRData/01_RAW/_T4_orig"
subfolders = ["TRONIC", "TRONIC2"]
target_path = "/Volumes/lhab_secure/02_LHAB/00_Data/00_MRData/01_RAW/T4/01_noIF"

os.chdir(root_path)

df = pd.read_csv("00_tp4_matching.txt", sep="\t")
df.set_index("TRONIC", inplace=True)

mapping = {"t1w_3d_tfe_puksenseV42": "t1w",
           "resting_pasenseV42": "fmri_pa",
           "resting2000_tarasenseV42": "fmri",
           "dti_nodif_apsenseV42": "dti_ap",
           "dti_nodif_pasenseV42": "dti_pa",
           "dti_high_iso_esenseV42": "dti",
           "flair_longtrclearV42": "2dflair",
           "3d_brain_view_flair_shcseV42": "3dflair",
           }

for old_id in df.T:
    info = []
    new_id = df.loc[old_id]["LHAB"]
    print(old_id, new_id)

    for f in subfolders:
        subject_source_folder = glob(os.path.join(root_path, f, "*" + old_id + "*"))
        if subject_source_folder:
            subject_source_folder = subject_source_folder[0]
            break

    subject_target_folder = os.path.join(target_path, "lhab_%s_t4_raw" % new_id)
    os.mkdir(subject_target_folder)
    print(subject_source_folder, subject_target_folder)

    os.chdir(subject_source_folder)
    file_list = glob("*")
    if file_list[0].startswith("lhab_"):
        # only update subject name
        for f_old in file_list:
            f_new = f_old.replace(old_id, new_id)
            cp_dest = os.path.join(subject_target_folder, f_new)
            print(f_old, cp_dest)
            shutil.copy(f_old, cp_dest)
            info.append("%s %s\n" % (f_old, cp_dest))

    else:  # make filename mapping
        for m_old, m_new in mapping.items():
            print(m_old, m_new)
            #            files= list(set(["_".join(f.split("_")[5:]).split(".")[0]) for f in glob("*" + m_old + "*")]))
            files = [f for f in glob("*" + m_old + "*")]
            files = list(set([f.split(".")[0] for f in files]))

            assert len(files) < 3, "something went wrong %s" % files
            abc = "abc"
            for n, f in enumerate(files):
                if len(files)>1:
                    n_str = "_" + abc[n]
                else:
                    n_str = ""

                for ext in ["par", "rec"]:
                    new_filename = "lhab_{id}_{mod}{n_str}_T4.{ext}".format(id=new_id, mod=m_new, n_str=n_str, ext=ext)
                    print(f, new_filename)
                    cp_source = f + "." + ext
                    cp_dest = os.path.join(subject_target_folder, new_filename)
                    shutil.copy(cp_source, cp_dest)
                    info.append("%s %s\n" % (cp_source, cp_dest))

    pdf = glob("*.pdf")
    if pdf:
        cp_dest = os.path.join(subject_target_folder, "lhab_{id}_T4.pdf".format(id=new_id))
        shutil.copy(pdf[0], cp_dest)
        info.append("%s %s\n" % (pdf[0], cp_dest))

    n_files_source = len(glob(subject_source_folder+"/*"))
    n_files_target = len(glob(subject_target_folder+"/*"))
    assert n_files_source==n_files_target, "not equal n files %s"%new_id

    with open(os.path.join(subject_target_folder, "info.txt"), "w") as fi:
        fi.write("".join(info))
