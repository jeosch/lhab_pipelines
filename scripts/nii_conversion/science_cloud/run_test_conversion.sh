# MRIDEFACE
python /data.nfs/code/bidswrapps/bidswrapps.py \
fliem/lhab_pipelines:v1.0.0.rc1 \
/data.nfs/LHAB/01_RAW /data.nfs/LHAB/NIFTI participant \
-pf /data.nfs/LHAB/01_RAW/00_PRIVATE_sub_lists/lhab_13subj.tsv \
--runscript_cmd "python /code/lhab_pipelines/scripts/nii_conversion/run_nii_conversion.py" \
-ra "--no-public_output --ds_version 1.0.0.rc1" \
-s lhab.conv.private.v1.0.0.rc1 -o /data.nfs/LHAB/logfiles/v1.0.0.rc1/logs_private -C 15 -c 2 -N


python /data.nfs/code/bidswrapps/bidswrapps.py \
fliem/lhab_pipelines:v1.0.0.rc1 \
/data.nfs/LHAB/01_RAW /data.nfs/LHAB/NIFTI participant \
-pf /data.nfs/LHAB/01_RAW/00_PRIVATE_sub_lists/lhab_13subj.tsv \
--runscript_cmd "python /code/lhab_pipelines/scripts/nii_conversion/run_nii_conversion.py" \
-ra "--ds_version 1.0.0.rc1" \
-s lhab.conv.public.v1.0.0.rc1 -o /data.nfs/LHAB/logfiles/v1.0.0.rc1/logs_public -C 15 -c 2 -N


