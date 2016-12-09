import json
import os

# docker stuff
import pandas as pd


def get_docker_container_name():
    docker_container_name = os.getenv("DOCKER_IMAGE")
    return docker_container_name


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

