import os

from . import utils
from lhab_pipelines.nii_conversion.utils import rotate_bvecs


def test_rotate_bvecs_angulation():
    data_path = os.path.join(os.path.dirname(utils.__file__), 'test_data')
    os.chdir(data_path)
    print("X" * 10)
    print(os.getcwd())

    import numpy as np
    from numpy.testing import assert_almost_equal

    bvecs_from_scanner = np.genfromtxt("bvecs.fromscanner")
    # test that with ang 0 leads to desired bvecs (compare with philipps)
    # test that angulation leads to desire bvecs (compare with philipps)
    test_list = [
        ("dwi/dwi.par", "dwi/dwi.bvec"),
        ("dwi_rot/dwi_rot.par", "dwi_rot/dwi_rot.bvec"),
    ]
    for par_file, goal_bvec_file in test_list:
        goal_bvecs = np.genfromtxt(goal_bvec_file)
        print(par_file, goal_bvec_file)
        rotated_bvecs = rotate_bvecs(bvecs_from_scanner, par_file)
        assert_almost_equal(rotated_bvecs, goal_bvecs, 5)

    # fail test
    par_file, goal_bvec_file = ("dwi/dwi.par", "dwi_rot/dwi_rot.bvec")
    goal_bvecs = np.genfromtxt(goal_bvec_file)
    rotated_bvecs = rotate_bvecs(bvecs_from_scanner, par_file)
    diff = np.abs((rotated_bvecs - goal_bvecs).sum())
    assert (diff > 0.1)

def test_get_public_sub_id():
    """test get_public_sub_id"""
    data_path = os.path.join(os.path.dirname(utils.__file__), 'test_data')
    os.chdir(data_path)
    new_id = utils.get_public_sub_id("lhab_abc2", "lut_test.tsv")
    assert (new_id == "lhabX0003"), "Test failed"