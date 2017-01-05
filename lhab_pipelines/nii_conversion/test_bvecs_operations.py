import os

from . import utils
from lhab_pipelines.nii_conversion.utils import rotate_bvecs

data_path = os.path.join(os.path.dirname(utils.__file__), 'test_data')

def test_rotate_bvecs_angulation():
    print("XXXXXXX")
    print(os.getcwd())
    import numpy as np
    from numpy.testing import assert_almost_equal

    bvecs_from_scanner = np.genfromtxt("test_data/bvecs.fromscanner")
    # test that with ang 0 leads to desired bvecs (compare with philipps)
    # test that angulation leads to desire bvecs (compare with philipps)
    test_list = [
        ("dwi/dwi.par", "dwi/dwi.bvec"),
        ("dwi_rot/dwi_rot.par", "dwi_rot/dwi_rot.bvec"),
    ]
    for par_file, goal_bvec_file in test_list:
        goal_bvecs = np.genfromtxt(os.path.join(data_path, goal_bvec_file))
        print(par_file, goal_bvec_file)
        rotated_bvecs = rotate_bvecs(bvecs_from_scanner, par_file)
        assert_almost_equal(rotated_bvecs, goal_bvecs, 5)

    # fail test
    par_file, goal_bvec_file = ("test_data/dwi/dwi.par", "test_data/dwi_rot/dwi_rot.bvec")
    goal_bvecs = np.genfromtxt(goal_bvec_file)
    rotated_bvecs = rotate_bvecs(bvecs_from_scanner, par_file)
    diff = np.abs((rotated_bvecs - goal_bvecs).sum())
    assert (diff > 0.1)
