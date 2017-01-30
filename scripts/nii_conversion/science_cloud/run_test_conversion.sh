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




# FREESURFER
python /data.nfs/code/bidswrapps/bidswrapps.py \
bids/freesurfer:v6.0.0-1 \
/data.nfs/LHAB/NIFTI/LHAB_1.0.0.rc1/sourcedata/ /data.nfs/LHAB/NIFTI/LHAB_1.0.0.rc1/derivates/freesurfer participant \
-ra "--license_key xx " \
-s lhab.freesurfer.v1.0.0.rc1 -o /data.nfs/LHAB/logfiles/freesurfer_v1.0.0.rc1 -w 60hours -C 15 -c 2 -N

# FREESURFER longfix test
python /data.nfs/code/bidswrapps/bidswrapps.py \
fliem/freesurfer:longfix \
/data.nfs/LHAB/NIFTI/LHAB_1.0.0.rc1/sourcedata/ /data.nfs/LHAB/NIFTI/LHAB_1.0.0.rc1/derivates/freesurfer.longfix \
participant \
-ra "--license_key xx " \
-s lhab.freesurfer.v1.0.0.rc1.longfix -o /data.nfs/LHAB/logfiles/freesurfer_v1.0.0.rc1.longfix -w 60hours -C 15 -c 2 -N


# demos
python /data.nfs/code/bidswrapps/bidswrapps.py \
fliem/lhab_pipelines:v1.0.0.rc1 \
/data.nfs/LHAB/01_RAW /data.nfs/LHAB/NIFTI group \
--volumes /data.nfs/code/lhab_pipelines /code/lhab_pipelines \
-pf /data.nfs/LHAB/01_RAW/00_PRIVATE_sub_lists/lhab_13subj.tsv \
--runscript_cmd "python /code/lhab_pipelines/scripts/nii_conversion/run_calc_demos.py" \
-ra "--ds_version 1.0.0.rc1 --pw "$PW \
-s lhab.conv.public.v1.0.0.rc1.demos -o /data.nfs/LHAB/logfiles/v1.0.0.rc1/logs_public.demos -C 15 -c 2 -N


