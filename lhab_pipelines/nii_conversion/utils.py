# fixme imports
from glob import glob
import os

import nibabel as nb
import numpy as np
import pandas as pd

from lhab_pipelines.utils import to_tsv, read_tsv, add_info_to_json, get_docker_container_name

# subject and session id related
def get_new_subject_id(old_subject_id):
    return old_subject_id[:4] + old_subject_id[5:]


def get_new_ses_id(old_ses_id):
    return "tp" + old_ses_id[1:]


def get_public_sub_id(old_sub_id, lut_file):
    "returns public sub_id string of style lhabX0001"
    df = pd.read_csv(lut_file, sep="\t")
    df = df.set_index("old_id")
    return df.loc[old_sub_id].values[0]


def test_get_public_sub_id():
    new_id = get_public_sub_id("lhab_abc2", "test_data/lut_test.tsv")
    assert (new_id == "lhabX0003"), "Test failed"


# BIDS related IO
def add_additional_bids_parameters_from_par(par_file, bids_file, parameters={"angulation": "Angulation"}):
    header_params = {}
    for param, param_label in parameters.items():
        header_params[param_label] = get_par_info(par_file, param)[param]  # out_parameter
    add_info_to_json(bids_file, header_params)


def update_scans_file(output_dir, bids_sub, bids_ses, bids_modality, out_filename, par_file):
    general_info, image_defs = read_par(par_file)
    acq_time = pd.to_datetime(general_info["exam_date"], format="%Y.%m.%d / %H:%M:%S")

    scans_file = os.path.join(output_dir, bids_sub, bids_sub + "_scans.tsv")
    if os.path.exists(scans_file):
        scans = read_tsv(scans_file)
    else:
        scans = pd.DataFrame([])  # columns=["ses_id", "filename", "acq_time"])
    scans = scans.append(
        {"ses_id": bids_ses, "filename": bids_ses + "/" + bids_modality + "/" + out_filename + ".nii.gz",
         "acq_time": acq_time}, ignore_index=True)
    scans = scans[["ses_id", "filename", "acq_time"]]
    to_tsv(scans, scans_file)


# PAR IO
def read_par(par_file):
    with open(par_file, "r") as fi:
        version, gen_dict, image_lines = nb.parrec._split_header(fi)
        general_info = _process_gen_dict(gen_dict)
        image_defs = nb.parrec._process_image_lines(image_lines, version)
    return general_info, image_defs


def get_par_info(par_file, parameters):
    from collections import OrderedDict
    if not isinstance(parameters, list):
        parameters = [parameters]
    out_parameters = OrderedDict()
    general_info, image_defs = read_par(par_file)

    for param in parameters:
        try:
            out_parameters.update({param: general_info[param]})
        except KeyError:
            try:
                out_parameters.update({param: image_defs[param]})
            except KeyError:
                raise
    return out_parameters


def _process_gen_dict(gen_dict):
    # Process `gen_dict` key, values into `general_info`
    ####
    """
    adapten from https://github.com/nipy/nibabel/blob/master/nibabel/parrec.py
    to work with msec in par file

    """

    import numpy as np

    _hdr_key_dict = {
        'Examination date/time': ('exam_date',),
        'Scan Duration [sec]': ('scan_duration', float),
        'Angulation midslice(ap,fh,rl)[degr]': ('angulation', float, (3,)),
    }

    slice_orientation_translation = {1: 'transverse',
                                     2: 'sagittal',
                                     3: 'coronal',
                                     }
    rec_dir = {'transverse': 2,
               'sagittal': 0,
               'coronal': 1,
               }

    general_info = {}
    for key, value in gen_dict.items():
        # get props for this hdr field
        if key in _hdr_key_dict.keys():
            props = _hdr_key_dict[key]
            # turn values into meaningful dtype
            if len(props) == 2:
                # only dtype spec and no shape
                value = props[1](value)
            elif len(props) == 3:
                # array with dtype and shape
                value = np.fromstring(value, props[1], sep=' ')
                # if shape is None, allow arbitrary length
                if props[2] is not None:
                    value.shape = props[2]
            general_info[props[0]] = value
    return general_info


# higher level conversion
def deface_data(bids_file, face_dir, nii_file, nii_output_dir, out_filename):
    old_wd = os.getcwd()
    os.chdir(nii_output_dir)
    tal_file = os.path.join(face_dir, "talairach_mixed_with_skull.gca")
    face_file = os.path.join(face_dir, "face.gca")
    defaced_file = os.path.join(nii_output_dir, out_filename + "_defaced.nii.gz")
    cmd = "mri_deface {in_file} {tal_file} {face_file} {defaced_file}".format(
        in_file=nii_file, tal_file=tal_file, face_file=face_file, defaced_file=defaced_file)
    print(cmd)
    os.system(cmd)
    deface_log_file = os.path.join(nii_output_dir, out_filename + "_defaced.nii.log")
    with open(deface_log_file) as fi:
        deface_log = fi.read()
    add_info_to_json(bids_file, {"deface_log": deface_log})
    os.remove(deface_log_file)
    # replace file with face with defaced file
    os.remove(nii_file)
    os.rename(defaced_file, nii_file)
    os.chdir(old_wd)


# BVECS OPERATIONS
def dwi_treat_bvecs(abs_par_file, bids_file, bvecs_from_scanner_file, nii_output_dir, par_file):
    '''
    replaces dcm2niix bvecs with rotated, own bvecs
    adds angulation to json
    '''
    add_additional_bids_parameters_from_par(abs_par_file, bids_file, {"angulation": "Angulation"})
    # remove dcm2niix bvecs and replace with own, rotated LAS bvecs
    bvecs_file = glob(os.path.join(nii_output_dir, "*.bvec"))[0]
    os.remove(bvecs_file)
    bvecs_from_scanner = np.genfromtxt(bvecs_from_scanner_file)
    rotated_bvecs_ras = rotate_bvecs(bvecs_from_scanner, par_file)
    rotated_bvecs_las = rotated_bvecs_ras.copy()
    rotated_bvecs_las[0] *= -1
    np.savetxt(bvecs_file, rotated_bvecs_las.T, fmt="%.5f")
    add_info_to_json(bids_file, {"bvecs_info": "rotated for angulation and in LAS space"})


# bvecs operations
def rotate_bvecs(bvecs_from_scanner, par_file):
    "takes bvecs from scanner, reads angulation from par_file and rotates bvecs"
    params = get_par_info(par_file, ["angulation", "slice orientation"])
    ap, fh, rl = params["angulation"]
    orient = params["slice orientation"][0]
    rotated_bvecs = rotate_vectors(bvecs_from_scanner, -ap, -fh, -rl, orient)
    return rotated_bvecs


def rotate_vectors(directions, ap, fh, rl, orient):
    # python implementation of matlab script rotDir
    #
    # function to rotate diffusion directions from a Philips *.par file
    # returns rotated bvecs in RAS space; test with LHAB data
    #  input:
    #            directions : diffusion directions ( nx3 matrix ) [ap fh rl]
    #            ap         : angulation AP ( in degrees )
    #            fh         : angulation FH ( in degrees )
    #            rl         : angulation RL ( in degrees )
    #            orient     : orientation ( TRA==1 / SAG==2 / COR==3 )
    #
    #  output:
    #            directions : rotatet diffusion directions ( nx3 matrix )
    #
    #
    #  BEWARE : Angulations are iverted versions of par file angulations
    #           the angulations are expected to be in degrees


    pi, sin, cos = np.pi, np.sin, np.cos
    ap = ap * pi / 180.
    fh = fh * pi / 180.
    rl = rl * pi / 180.

    # % create rotation matrices
    rotap = np.array([[1, 0, 0],
                      [0, cos(ap), -sin(ap)],
                      [0, sin(ap), cos(ap)]])

    rotfh = np.array([[cos(fh), 0, sin(fh)],
                      [0, 1, 0],
                      [-sin(fh), 0, cos(fh)]])

    rotrl = np.array([[cos(rl), -sin(rl), 0],
                      [sin(rl), cos(rl), 0],
                      [0, 0, 1]])

    # do rotation in the patient's reference frame
    rot = np.dot(np.dot(rotfh, rotap), rotrl)
    tmp = directions.copy()
    for i in np.arange(np.size(directions, 0)):
        tmp[i, :] = (np.dot(rot, directions[i, :].T)).T
    directions = tmp.copy()

    # permutation (transform AP-FH-RL into X-Y-Z)
    tmp = directions.copy()
    directions[:, 0] = - tmp[:, 0]  # AP -> -X
    directions[:, 1] = tmp[:, 2]  # RL ->  Y
    directions[:, 2] = - tmp[:, 1]  # FH -> -Z

    # permutation (transform X-Y-Z into iX-iY-iZ)
    tmp = directions.copy()
    if 1 == orient:
        directions[:, 0] = tmp[:, 1]
        directions[:, 1] = - tmp[:, 0]
        directions[:, 2] = - tmp[:, 2]
    elif 2 == orient:
        directions[:, 0] = - tmp[:, 0]
        directions[:, 1] = tmp[:, 2]
        directions[:, 2] = - tmp[:, 1]
    elif 3 == orient:
        directions[:, 0] = tmp[:, 1]
        directions[:, 1] = tmp[:, 2]
        directions[:, 2] = - tmp[:, 0]

    # flip y
    directions[:, 1] *= -1

    return directions

