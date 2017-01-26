import os, shutil

if os.path.isdir("01_RAW"):
    shutil.rmtree("01_RAW")
os.makedirs("01_RAW")

tps = ["T1", "T3"]
id = "phan"
mapping = {"lhab_{sub}_fmri_{tp}": "phantom_varscale",
           "lhab_{sub}_fmri_pa_{tp}": "phantom_varscale",
           "lhab_{sub}_dti_b0_{tp}": "phantom_varscale",
           "lhab_{sub}_2dflair_{tp}": "Survey_1_1",
           "lhab_{sub}_3dflair_{tp}": "Survey_1_1",
           "lhab_{sub}_t2w_{tp}": "phantom_varscale",
           "lhab_{sub}_t1w_{run}_{tp}": "Survey_1_1",
           "lhab_{sub}_dti_{tp}": "ph_26012017_1153144_4_1_dtihighisoeV4",
           "lhab_{sub}_dti_ap_{tp}": "ph_26012017_1151068_2_1_dtinodifapV4",
           "lhab_{sub}_dti_pa_{tp}": "ph_26012017_1152106_3_1_dtinodifpaV4",
           }

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
data_dir = os.path.join(base_dir, "data")

os.chdir(output_dir)
print(os.path.relpath(os.path.join(data_dir, "00_face")), "00_face")
os.symlink(os.path.relpath(os.path.join(data_dir, "00_face")), "00_face")
print(os.path.relpath(os.path.join(data_dir, "00_bvecs")), "00_bvecs")
os.symlink(os.path.relpath(os.path.join(data_dir, "00_bvecs")), "00_bvecs")


print(mapping)
for tp in tps:
    output_dir = os.path.join(base_dir, "01_RAW", tp, "01_noIF", "lhab_{sub}_{tp}_raw".format(sub=id, tp=tp.lower()))

    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)
    os.chdir(output_dir)

    for seq, phantom_base in mapping.items():
        print(phantom_base, seq)
        for ext in [".par", ".rec"]:
            os.symlink(os.path.relpath(os.path.join(data_dir, phantom_base + ext)),
                       seq.format(sub=id, tp=tp, run=run) + ext)
            print(os.path.relpath(os.path.join(data_dir, phantom_base + ext)),
                  seq.format(sub=id, tp=tp, run=run) + ext)
    print("")
