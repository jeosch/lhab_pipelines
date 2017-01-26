python /data.nfs/code/bidswrapps/bidswrapps.py \
fliem/lhab_pipelines:v1.0.0.dev11 \
/data.nfs/LHAB/01_RAW /data.nfs/LHAB/NIFTI participant \
-pf /data.nfs/LHAB/01_RAW/00_PRIVATE_sub_lists/lhab_13subj.tsv \
--runscript_cmd "python /code/lhab_pipelines/scripts/nii_conversion/run_nii_conversion.py" \
-ra "--no-public_output --ds_version 1.0.0.dev11" \
-s lhab.conv.private.v1.0.0.dev11 -o /data.nfs/LHAB/logfiles/v1.0.0.dev11/logs_private -C 15 -c 2 -N


python /data.nfs/code/bidswrapps/bidswrapps.py \
fliem/lhab_pipelines:v1.0.0.dev11 \
/data.nfs/LHAB/01_RAW /data.nfs/LHAB/NIFTI participant \
-pf /data.nfs/LHAB/01_RAW/00_PRIVATE_sub_lists/lhab_13subj.tsv \
--runscript_cmd "python /code/lhab_pipelines/scripts/nii_conversion/run_nii_conversion.py" \
-ra "--ds_version 1.0.0.dev11" \
-s lhab.conv.public.v1.0.0.dev11 -o /data.nfs/LHAB/logfiles/v1.0.0.dev11/logs_public -C 15 -c 2 -N


# FAST
python /data.nfs/code/bidswrapps/bidswrapps.py \
fliem/lhab_pipelines:v1.0.0.dev11 \
/data.nfs/LHAB/01_RAW /data.nfs/LHAB/NIFTI_fast participant \
--volume /data.nfs/code/lhab_pipelines:/code/lhab_pipelines \
-pf /data.nfs/LHAB/01_RAW/00_PRIVATE_sub_lists/lhab_13subj.tsv \
--runscript_cmd "python /code/lhab_pipelines/scripts/nii_conversion/run_nii_conversion_fast.py" \
-ra "--no-public_output --ds_version 1.0.0.dev11" \
-s lhab.conv.private.v1.0.0.dev11_fast -o /data.nfs/LHAB/logfiles/v1.0.0.dev11_fast/logs_private -C 15 -c 2 -N