
## run_nii_conversion.py
performs the parrec 2 nifti conversion (on sc)

```
swv=v1.0.0.rc6
dsv=v1.0.0.rc3
sfile=lhab_13subj.tsv

screen python `which bidswrapps_start.py` \
fliem/lhab_pipelines:${swv} \
/data.nfs/LHAB/01_RAW /data.nfs/LHAB/NIFTI participant \
-pf /data.nfs/LHAB/01_RAW/00_PRIVATE_sub_lists/${sfile} \
--runscript_cmd "python /code/lhab_pipelines/scripts/nii_conversion/run_nii_conversion.py" \
-ra "--no-public_output --ds_version ${dsv}" \
-s cloudsessions/lhab.conv.private.${dsv} -o /data.nfs/LHAB/logfiles/${dsv}/logs_private -C 15 -c 1


screen python `which bidswrapps_start.py` \
fliem/lhab_pipelines:${swv} \
/data.nfs/LHAB/01_RAW /data.nfs/LHAB/NIFTI participant \
-pf /data.nfs/LHAB/01_RAW/00_PRIVATE_sub_lists/${sfile} \
--runscript_cmd "python /code/lhab_pipelines/scripts/nii_conversion/run_nii_conversion.py" \
-ra "--ds_version ${dsv}" \
-s cloudsessions/lhab.conv.public.${dsv} -o /data.nfs/LHAB/logfiles/${dsv}/logs_public -C 15 -c 1


```




## run_post_conversion_routines.py
checks data and reduces subjects data

```
swv=v1.0.0.rc6
dsv=v1.0.0.rc3
vshort=rc3
sfile=lhab_13subj.tsv


docker run --rm -ti \
-v /Volumes/lhab_raw/01_RAW:/data/in \
-v /Volumes/lhab_raw/Nifti/${vshort}/NIFTI/:/data/out \
fliem/lhab_pipelines:${swv} python /code/lhab_pipelines/scripts/nii_conversion/run_post_conversion_routines.py /data/in /data/out --participant_file /data/in/00_PRIVATE_sub_lists/${sfile} --ds_version ${dsv}



docker run --rm -ti \
-v /Volumes/lhab_raw/01_RAW:/data/in \
-v /Volumes/lhab_raw/Nifti/${vshort}/NIFTI/:/data/out \
fliem/lhab_pipelines:${swv} python /code/lhab_pipelines/scripts/nii_conversion/run_post_conversion_routines.py /data/in /data/out --participant_file /data/in/00_PRIVATE_sub_lists/${sfile} --ds_version ${dsv} --no-public_output
```


#

## freesurfer
```
dsv=v1.0.0.rc3
screen python `which bidswrapps_start.py` \
bids/freesurfer:v6.0.0-2 \
/data.nfs/LHAB/NIFTI/LHAB_${dsv}/sourcedata/ /data.nfs/LHAB/NIFTI/LHAB_${dsv}/derivates/freesurfer participant \
-ra "--license_key ~/fs.key --n_cpus 8" \
-s cloudsessions/lhab.freesurfer.${dsv} -o /data.nfs/LHAB/logfiles/freesurfer_${dsv} -w 60hours -C 15 -c 8

```

## tracula
```
dsv=v1.0.0.rc3
screen python `which bidswrapps_start.py` \
bids/tracula:v6.0.0-1 \
/data.nfs/LHAB/NIFTI/LHAB_${dsv}/sourcedata/ /data.nfs/LHAB/NIFTI/LHAB_${dsv}/derivates/tracula participant \
-ra "--license_key ~/fs.key --freesurfer_dir /data/freesurfer" \
--volume /data.nfs/LHAB/NIFTI/LHAB_${dsv}/derivates/freesurfer/:/data/freesurfer \
-s cloudsessions/lhab.tracula.${dsv} -o /data.nfs/LHAB/logfiles/tracula_${dsv} -w 60hours -C 15 -c 2
```