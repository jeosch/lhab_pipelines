import os
from glob import glob
import shutil

data_dir = os.getenv("LHAB_DIR")
if not data_dir:
    raise Exception("env LHAB_DIR not set")

fs_base_dir = os.path.join(data_dir, "00_Data/4ScienceCloud/Freesurfer/data_all_results/data_all/")
bids_fs_target_dir = os.path.join(data_dir, "00_Data/4Franz/tracula_bids_in_data/freesurfer")

if os.path.exists(bids_fs_target_dir):
    shutil.rmtree(bids_fs_target_dir)
os.makedirs(bids_fs_target_dir)
os.chdir(bids_fs_target_dir)

for r in sorted(glob(os.path.join(fs_base_dir, "run*"))):
    # base template
    base_template_source_folder = glob(os.path.join(r, "output", "lhab*.base"))[0]
    slim_sub_id = base_template_source_folder.split("_")[-1][:4]
    bids_sub = "sub-lhab{slim_sub_id}".format(slim_sub_id=slim_sub_id)

    print(bids_sub)
    base_name = "{bids_sub}.base".format(bids_sub=bids_sub)
    base_template_target_folder = os.path.join(bids_fs_target_dir, base_name)
    os.symlink(base_template_source_folder, base_template_target_folder)

    # cross sectional data
    cross_search_str = os.path.join(r, "output", "lhab_{slim_sub_id}.cross.*tp".format(slim_sub_id=slim_sub_id))
    for cross_source_folder in sorted(glob(cross_search_str)):
        slim_ses_id = cross_source_folder.split(".")[-1][0]
        bids_ses = "ses-tp{slim_ses_id}".format(slim_ses_id=slim_ses_id)
        cross_name = "{bids_sub}_{bids_ses}".format(bids_sub=bids_sub, bids_ses=bids_ses)
        cross_target_folder = os.path.join(bids_fs_target_dir, cross_name)
        os.symlink(cross_source_folder, cross_target_folder)

    # long data
    long_search_str = os.path.join(r, "output", "lhab_{slim_sub_id}.cross.*tp.long.lhab_{slim_sub_id}.base".format(
        slim_sub_id=slim_sub_id))
    for long_source_folder in sorted(glob(long_search_str)):
        slim_ses_id = long_source_folder.split(".")[2][0]
        bids_ses = "ses-tp{slim_ses_id}".format(slim_ses_id=slim_ses_id)
        long_name = "{bids_sub}_{bids_ses}.long.{base_name}".format(bids_sub=bids_sub, bids_ses=bids_ses, base_name=base_name)
        "sub-<subject_label>_ses-<session_label>.long.sub-<subject_label>"
        long_target_folder = os.path.join(bids_fs_target_dir, long_name)
        os.symlink(long_source_folder, long_target_folder)
