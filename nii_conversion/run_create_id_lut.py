"""
Script builds file list by going through raw folder.
A lookup table (LUT) matching old id and new id is created and saved as tsv file
old_id style: lhab_abcd
new_id style: lhabX0001
"""

import os
import glob, random
import pandas as pd


base_dir = "/data/"
raw_dir = os.path.join(base_dir, "raw")
output_dir = os.path.join(base_dir, "nifti", "00_sub_id_lut")
face_dir = os.path.join(raw_dir, "face")

ses_id_list = ["T1", "T2", "T3", "T4", "T5"]
in_ses_folder = "01_noIF"

#
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# get subject list
raw_subjects_list = []
for ses in ses_id_list:
    search_dir = os.path.join(raw_dir, ses, in_ses_folder)
    os.chdir(search_dir)
    raw_subjects_list += sorted(glob.glob("lhab*"))
old_subject_id_list = sorted(list(set([s[:9] for s in raw_subjects_list])))


new_id = []
for i in range(1, 1000):
    new_id.append('lhabX{:04d}'.format(i))

# for good measures, shuffle
n_sub = len(old_subject_id_list)
new_id_used = new_id[:n_sub]
random.shuffle(new_id_used)
new_id_spare = new_id[n_sub:]
new_id = new_id_used + new_id_spare

old_id = old_subject_id_list + [None]*len(new_id_spare)
df = pd.DataFrame({"old_id": old_id, "new_id": new_id})
df = df.set_index("old_id")

out_filename = os.path.join(output_dir, "new_sub_id_lut.tsv")
if os.path.exists(out_filename):
    raise Exception("File {f} already exists. I did nothing."
                    "Delete and run script again!".format(f=out_filename))
df.to_csv(out_filename, sep="\t")
print("Subject ID LUT written to {}".format(out_filename))

os.chmod(out_filename, 0o444)
print("Permission set to read only")

