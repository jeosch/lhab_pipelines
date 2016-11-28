from glob import glob
import os
in_data = "/data/tracula_in_data/sourcedata"
out_data = "/data/tracula_out_data"
os.chdir(in_data)

sub_list = glob("sub*")
failed_sub = []
ok_sub = []

for s in sub_list:
    if not os.path.exists(os.path.join(out_data, "run_"+ s)):
        failed_sub.append(s)
    else:
        ok_sub.append(s)

print(failed_sub)
