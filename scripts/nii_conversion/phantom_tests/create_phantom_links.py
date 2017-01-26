import os, shutil

phantom_base = "phantom_varscale"

if os.path.isdir("01_RAW"):
    shutil.rmtree("01_RAW")
os.makedirs("01_RAW")

tps = ["T1", "T3"]
id = "phan"
mapping = {"*resting2000*": "lhab_{sub}_fmri_{tp}",
           "*resting_pa*": "lhab_{sub}_fmri_pa_{tp}",
           # "*dti_high*": "lhab_{sub}_dti_{tp}",
           # "*dti_nodif_ap*": "lhab_{sub}_dti_ap_{tp}",
           # "*dti_nodif_pa*": "lhab_{sub}_dti_pa_{tp}",
           "*b0map*": "lhab_{sub}_dti_b0_{tp}",
           "*flair_long*": "lhab_{sub}_2dflair_{tp}",
           "*3d_brain_view*": "lhab_{sub}_3dflair_{tp}",
           "*t2w*": "lhab_{sub}_t2w_{tp}",
           "*t1w*": "lhab_{sub}_t1w_{run}_{tp}"}

slist_dir = os.path.join("01_RAW", "00_PRIVATE_sub_lists")
os.makedirs(slist_dir)
with open(os.path.join(slist_dir, "new_sub_id_lut.tsv"), "w") as fi:
    fi.write("old_id\tnew_id\n"
             "lhab_phan\tlhabX9999\n")
with open(os.path.join(slist_dir, "phan_id_list.tsv"), "w") as fi:
    fi.write("sub_id\nlhab_phan")

run = "a"
base_dir = os.getcwd()

# linke face data
output_dir = os.path.join(base_dir, "01_RAW")
os.chdir(output_dir)
print(os.path.relpath(os.path.join(base_dir, "00_face")), "00_face")
os.symlink(os.path.relpath(os.path.join(base_dir, "00_face")), "00_face")

for tp in tps:
    output_dir = os.path.join(base_dir, "01_RAW", tp, "01_noIF", "lhab_{sub}_{tp}_raw".format(sub=id, tp=tp.lower()))

    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)
    os.chdir(output_dir)

    for seq in mapping.values():
        print(seq)
        for ext in [".par", ".rec"]:
            # print(phantom_base + ext, os.path.join(output_dir, seq.format(sub=id, tp=tp.lower(), run=run) + ext))
            os.symlink(os.path.relpath(os.path.join(base_dir, phantom_base + ext)),
                       seq.format(sub=id, tp=tp, run=run) + ext)
