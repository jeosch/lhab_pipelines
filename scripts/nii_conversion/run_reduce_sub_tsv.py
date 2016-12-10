from lhab_pipelines.utils import reduce_sub_files

bids_dir = "/data/nifti/sourcedata"

output_file = "participants.tsv"
sub_file = "participant.tsv"
reduce_sub_files(bids_dir, output_file, sub_file)


output_file = "scans.tsv"
sub_file = "scans.tsv"
reduce_sub_files(bids_dir, output_file, sub_file)
