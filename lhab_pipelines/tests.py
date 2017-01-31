from . import utils
import pandas as pd
import os

def test_read_protected_file():
    """opens text file from protected zip"""
    corr_df = pd.DataFrame(index=["s1", "s2"], columns={"info": [10, 20]})
    data_path = os.path.join(os.path.dirname(utils.__file__), 'test_data')
    df = utils.read_protected_file(os.path.join(data_path, "prot.zip"), "pw", "tab.tsv")
    assert (df==df).all().all(), "prot file not equal to template"