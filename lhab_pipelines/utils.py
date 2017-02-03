import json
import os
import zipfile
from collections import OrderedDict
from io import StringIO

import numpy
import pandas as pd


def to_tsv(df, filename, header=True):
    df.to_csv(filename, sep="\t", index=False, header=header)


def read_tsv(filename, no_header=False):
    if no_header:
        return pd.read_csv(filename, sep="\t", header=None)
    else:
        return pd.read_csv(filename, sep="\t")


def get_json(bids_file):
    with open(bids_file) as fi:
        bids_data = json.load(fi)
    return bids_data


def add_info_to_json(bids_file, new_info, create_new=False):
    # if create_new=True: if file does not exist, file is created and new_info is written out
    if os.path.exists(bids_file):
        bids_data = get_json(bids_file)
    elif (not os.path.exists(bids_file)) and create_new:
        bids_data = {}
    else:
        raise FileNotFoundError("%s does not exist. Something migth be wrong. If a file should create, "
                                "use create_new=True " % bids_file)

    for k, v in new_info.items():
        if isinstance(v, numpy.ndarray):
            new_info[k] = v.tolist()
    bids_data.update(new_info)

    with open(bids_file, "w") as fi:
        json.dump(OrderedDict(sorted(bids_data.items())), fi, indent=4)


def read_protected_file(zfile, pwd, datafile):
    """
    opens encrypted zipfile and reads table sep. datafile (txt)
    returns a data frame
    """
    pwd = bytes(pwd, 'utf-8')
    fi = zipfile.ZipFile(zfile)
    data = fi.read(datafile, pwd=pwd)
    data = data.decode()
    fi.close()
    df = pd.read_csv(StringIO(data), sep="\t")
    df.set_index("subject_id", inplace=True)
    return df
