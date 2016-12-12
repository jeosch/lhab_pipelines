import json
import os
import warnings

# docker stuff
import pandas as pd
from bids.grabbids import BIDSLayout


def get_docker_container_name():
    docker_container_name = os.getenv("DOCKER_IMAGE")
    return docker_container_name

def check_docker_container_version(requested_v):
    actual_v = get_docker_container_name()
    if actual_v:
        if not actual_v == requested_v:
            raise RuntimeError("Requested docker version: %s, but running %s"%(requested_v, actual_v))
        else:
            print("Running docker: %s" %actual_v)
    else:
        warnings.warn("Not running in Docker env!")

def to_tsv(df, filename):
    df.to_csv(filename, sep="\t", index=False)


def read_tsv(filename):
    return pd.read_csv(filename, sep="\t")


def get_json(bids_file):
    with open(bids_file) as fi:
        bids_data = json.load(fi)
    return bids_data


def add_info_to_json(bids_file, new_info):
    import numpy
    bids_data = get_json(bids_file)
    for k,v in new_info.items():
        if isinstance(v, numpy.ndarray):
            new_info[k] = v.tolist()
    bids_data.update(new_info)

    with open(bids_file, "w") as fi:
        json.dump(bids_data, fi, indent=4)


def reduce_sub_files(bids_dir, output_file, sub_file):
    df = pd.DataFrame([])
    layout = BIDSLayout(bids_dir)
    files = layout.get(extensions=sub_file)
    for file in [f.filename for f in files]:
        print(file)
        df_ = read_tsv(file)
        df = pd.concat((df, df_))

    to_tsv(df, os.path.join(bids_dir, output_file))