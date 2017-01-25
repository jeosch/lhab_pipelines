import argparse, os, shutil
from glob import glob
import datetime
from warnings import warn

# TODO physio

parser = argparse.ArgumentParser("renames files from scanner for 01_RAW."
                                 "Usage: change into raw data folder and call script.")
parser.add_argument('lhab_id', help='e.g. 12ab')
args = parser.parse_args()

print("X X " * 10)
print(os.getcwd(), args.lhab_id)
print("X X " * 10 + "\n\n")

tp = "T5"
mapping = {"*resting2000*": "lhab_{sub}_fmri_{tp}",
           "*resting_pa*": "lhab_{sub}_fmri_pa_{tp}",
           "*dti_high*": "lhab_{sub}_dti_{tp}",
           "*dti_nodif_ap*": "lhab_{sub}_dti_ap_{tp}",
           "*dti_nodif_pa*": "lhab_{sub}_dti_pa_{tp}",
           "*b0map*": "lhab_{sub}_dti_b0_{tp}",
           "*flair_long*": "lhab_{sub}_2dflair_{tp}",
           "*3d_brain_view*": "lhab_{sub}_3dflair_{tp}",
           "*t2w*": "lhab_{sub}_t2w_{tp}",
           "*t1w*": "lhab_{sub}_t1w_{run}_{tp}"}

output_dir = os.path.join(os.getcwd(), "../../data_quarant", "lhab_{sub}_{tp}_raw".format(sub=args.lhab_id,
                                                                                          tp=tp.lower()))
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
print(output_dir)

for source_str, target_str in mapping.items():
    g = glob(source_str + ".par")

    if len(g) > 0:
        if source_str == "*t1w*":
            runs = ["a", "b"]
            for i, f in enumerate(g):
                run = runs[i]
                f_source = ".".join(f.split(".")[:-1])
                f_target = os.path.join(output_dir, target_str.format(sub=args.lhab_id, tp=tp, run=run))

                for ext in [".par", ".rec"]:
                    shutil.copy(f_source + ext, f_target + ext)
                    print("copy: ", f_source + ext, f_target + ext)

        elif len(g) == 1:
            f_source = ".".join(g[0].split(".")[:-1])
            f_target = os.path.join(output_dir, target_str.format(sub=args.lhab_id, tp=tp))

            for ext in [".par", ".rec"]:
                shutil.copy(f_source + ext, f_target + ext)
                print("copy: ", f_source + ext, f_target + ext)

            if "resting" in source_str:  # check for physiology logs
                source_ts = g[0].split("_")[2]
                par_h, par_m, par_s = source_ts[:2], source_ts[2:4], source_ts[4:6]
                par_time = datetime.datetime(2001, 1, 1, int(par_h), int(par_m), int(par_s))
                log_time = par_time - datetime.timedelta(0, 14)
                log_str = "SCANPHYSLOG*{:%H%M%S}.log".format(log_time)
                phys_files = glob(log_str)

                # if that doesnt work try +- 1 second
                for d in [-1,1]:
                    log_time = par_time - datetime.timedelta(0, 14+d)
                    log_str = "SCANPHYSLOG*{:%H%M%S}.log".format(log_time)
                    phys_files += glob(log_str)

                if len(phys_files) == 0:
                    warn("No log file found %s %s" % (source_str, log_str))
                elif len(phys_files) > 1:
                    raise Exception("more than one logfiles found. exit. %s %s" % (source_str, log_str))
                else:
                    f_source = phys_files[0]
                    f_target = os.path.join(output_dir, target_str.format(sub=args.lhab_id, tp=tp) + "_physio.log")
                    shutil.copy(f_source, f_target)
                    print("copy: ", f_source, f_target)


        else:
            raise Exception("somethings not right %s" % g)





    else:
        pass
