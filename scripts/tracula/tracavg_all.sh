#!/bin/bash
out_list_dir=/data/tracula_collect_tracts
out_trac_dir=/data/tracula_collect_tracts/out_overall
out_overall_dir=/data/tracula_collect_tracts/out_voxel
mkdir -p $out_trac_dir
mkdir -p $out_overall_dir

DTI_DATA=/data/tracula_out_data

#cd ${DTI_DATA}
#write a list with paths to the diffusion averages for each tract
for tractpath in rh.unc lh.cst rh.cst lh.ilf rh.ilf fmajor fminor lh.atr rh.atr lh.cab rh.cab lh.ccg rh.ccg lh.slfp rh.slfp lh.slft rh.slft lh.unc
do
#tract=$(echo ${tractpath} | sed "s/...$//g")
tract=$tractpath
ls ${DTI_DATA}/run_sub-lhab*/output/sub-lhab*_ses-tp*.long.sub-lhab*.base/dpath/${tract}*_avg33_mni_bbr/pathstats.overall.txt >> ${out_list_dir}/${tract}.list.txt
done

#convert the list into a excel table for each tract
for tract in fmajor fminor lh.atr rh.atr lh.cab rh.cab lh.ccg rh.ccg lh.slfp rh.slfp lh.slft rh.slft lh.unc rh.unc lh.cst rh.cst lh.ilf rh.ilf
do
tractstats2table --load-pathstats-from-file ${out_list_dir}/${tract}.list.txt --overall --tablefile ${out_trac_dir}/${tract}.all.table.csv
done
echo "all done!"


for tract in fmajor fminor lh.atr rh.atr lh.cab rh.cab lh.ccg rh.ccg lh.slfp rh.slfp lh.slft rh.slft lh.unc rh.unc lh.cst rh.cst lh.ilf rh.ilf
do
for m in AD RD MD FA
do
echo $tract $m
tractstats2table --load-pathstats-from-file ${out_list_dir}/${tract}.list.txt --byvoxel --byvoxel-measure=${m} --tablefile ${out_overall_dir}/${tract}.${m}.all.table.csv
done
done
echo "all done!"
