
python /home/ubuntu/gtrac_long_repo/gc3pie/gc3apps/inapic/bidsapps.py \
"--volume /data.nfs/code/:/code fliem/lhab_docker:v0.8.8.dev.nolhpipe python /code/lhab_pipelines/scripts/nii_conversion/run_nii_conversion.py" /data.nfs/bidsapps_test/01_RAW /data.nfs/bidsapps_test/ participant \
-pf /data.nfs/bidsapps_test/01_RAW/00_PRIVATE_sub_lists/lhab_10subj.tsv \
--ra "--no-public_output" \
-vvv -s testbids.conv -o /data.nfs/bidsapps_test/logfiles -N -C 15 -c 2
