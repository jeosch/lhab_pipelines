python /data.nfs/code/bidswrapps/bidswrapps.py \
fliem/lhab_docker:v0.8.8.dev.nolhpipe \
/data.nfs/LHAB/01_RAW /data.nfs/LHAB/NIFTI participant \
--volume /data.nfs/code/:/code \
-pf /data.nfs/LHAB/01_RAW/00_PRIVATE_sub_lists/lhab_13subj.tsv \
--runscript_cmd "python /code/lhab_pipelines/scripts/nii_conversion/run_nii_conversion.py" \
-ra "--no-public_output --ds_version 1.0.0.dev " \
-s testbids.conv.private -o /data.nfs/LHAB/logfiles/logs_private -C 15 -c 2 -N


python /data.nfs/code/bidswrapps/bidswrapps.py \
fliem/lhab_docker:v0.8.8.dev.nolhpipe \
/data.nfs/LHAB/01_RAW /data.nfs/LHAB/NIFTI participant \
--volume /data.nfs/code/:/code \
-pf /data.nfs/LHAB/01_RAW/00_PRIVATE_sub_lists/lhab_13subj.tsv \
--runscript_cmd "python /code/lhab_pipelines/scripts/nii_conversion/run_nii_conversion.py" \
-ra "--ds_version 1.0.0.dev " \
-s testbids.conv.public -o /data.nfs/LHAB/logfiles/logs_public -C 15 -c 2 -N
