python /data.nfs/code/bidswrapps/bidswrapps.py \
"--volume /data.nfs/code/:/code fliem/lhab_docker:v0.8.8.dev.nolhpipe python /code/lhab_pipelines/scripts/nii_conversion/run_nii_conversion.py" /data.nfs/LHAB/01_RAW /data.nfs/LHAB/ participant \
-pf /data.nfs/LHAB/01_RAW/00_PRIVATE_sub_lists/lhab_13subj.tsv \
-ra "--no-public_output " \
-s testbids.conv -o /data.nfs/LHAB/logfiles -C 15 -c 2 -N
