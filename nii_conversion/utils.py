#fixme imports

import glob
import os
import json
import numpy as np
import datetime as dt
import pandas as pd

#from .read_par import read_par, get_par_info
from nipype.interfaces.dcm2nii import Dcm2niix
from nipype.interfaces.fsl import Reorient2Std


def run_conversions(old_subject_id, old_ses_id, abs_subject_folder, output_dir, info_list,
                    bvecs_from_scanner_file=None):
    os.chdir(abs_subject_folder)
    for infodict in info_list:
        convert_modality(old_subject_id, old_ses_id, output_dir, bvecs_from_scanner_file=bvecs_from_scanner_file, **infodict)


def to_tsv(df, filename):
    df.to_csv(filename, sep="\t", index=False)


def read_tsv(filename):
    return pd.read_csv(filename, sep="\t")


def get_new_subject_id(old_subject_id):
    return old_subject_id[:4] + old_subject_id[5:]


def get_new_ses_id(old_ses_id):
    return "tp" + old_ses_id[1:]


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


def add_additional_bids_parameters_from_par(par_file, bids_file, parameters={"angulation": "Angulation"}):
    header_params = {}
    for param, param_label in parameters.items():
        header_params[param_label] =get_par_info(par_file, param)[param]# out_parameter
    add_info_to_json(bids_file, header_params)


def convert_modality(old_subject_id, old_ses_id, output_dir, bids_name, bids_modality,
                     search_str, bvecs_from_scanner_file=None, reorient2std=True, task=None, direction=None, only_use_last=False):
    new_ses_id = get_new_ses_id(old_ses_id)
    bids_sub = "sub-" + get_new_subject_id(old_subject_id)
    bids_ses = "ses-" + new_ses_id
    mapping_file = os.path.join(output_dir, bids_sub, "par2nii_mapping.txt")

    par_file_list = glob.glob("*" + search_str + "*.par")
    if par_file_list:
        nii_output_dir = os.path.join(output_dir, bids_sub, bids_ses, bids_modality)
        if not os.path.exists(nii_output_dir):
            os.makedirs(nii_output_dir)

        if only_use_last:
            par_file_list = par_file_list[-1:]

        for run_id, par_file in enumerate(par_file_list, 1):
            abs_par_file = os.path.abspath(par_file)
            abs_rec_file = os.path.splitext(abs_par_file)[0] + ".rec"
            assert os.path.exists(abs_rec_file), "REC file does not exist %s" % abs_rec_file

            bids_run = "run-" + str(run_id)
            out_components = [bids_sub, bids_ses]
            if task:
                out_components += ["task-%s" % task]
            if direction:
                out_components += ["dir-%s" % direction]

            out_components += [bids_run, bids_name]
            out_filename = "_".join(out_components)
            nii_file = os.path.join(nii_output_dir, out_filename + ".nii.gz")
            assert not os.path.exists(nii_file), "file exists. STOP. %s" % nii_file

            converter = Dcm2niix()
            converter.inputs.source_names = [abs_par_file]
            converter.inputs.bids_format = True
            converter.inputs.compress = 'i'
            converter.inputs.has_private = True
            converter.inputs.out_filename = out_filename
            converter.inputs.output_dir = nii_output_dir
            converter_results = converter.run()
            bids_file = converter_results.outputs.bids

            # add additional information to json
            add_additional_bids_parameters_from_par(abs_par_file, bids_file, {"scan_duration": "ScanDurationSec"})

            # write par 2 nii mapping file
            with open(mapping_file, "a") as fi:
                fi.write("%s %s\n"%(abs_par_file, nii_file))

            # add angulation to json for dwi
            if bids_name == "dwi":
                add_additional_bids_parameters_from_par(abs_par_file, bids_file, {"angulation": "Angulation"})
                # remove dcm2niix bvecs and replace with own, rotated LAS bvecs
                bvecs_file = glob.glob(os.path.join(nii_output_dir, "*.bvec"))[0]
                os.remove(bvecs_file)
                bvecs_from_scanner = np.genfromtxt(bvecs_from_scanner_file)
                rotated_bvecs_ras = rotate_bvecs(bvecs_from_scanner, par_file)
                rotated_bvecs_las = rotated_bvecs_ras.copy()
                rotated_bvecs_las[0] *= -1
                np.savetxt(bvecs_file, rotated_bvecs_las, fmt="%.5f")
                add_info_to_json(bids_file, {"bvecs_info": "rotated for angulation and in LAS space"})

            # add task and number of volumes to json file for rest
            if task:
                add_info_to_json(bids_file, {"TaskName": task})

            if reorient2std:
                reorient = Reorient2Std()
                reorient.inputs.in_file = converter_results.outputs.converted_files
                reorient.inputs.out_file = converter_results.outputs.converted_files
                reorient_results = reorient.run()
            update_scans_file(output_dir, bids_sub, bids_ses, bids_modality, out_filename, par_file)


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

    import numpy as np
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


def rotate_bvecs_angulation_tests():
    import numpy as np
    from numpy.testing import assert_almost_equal

    bvecs_from_scanner = np.genfromtxt("test_data/bvecs.fromscanner")
    # test that with ang 0 leads to desired bvecs (compare with philipps)
    # test that angulation leads to desire bvecs (compare with philipps)
    test_list = [
        ("test_data/dwi/dwi.par", "test_data/dwi/dwi.bvec"),
        ("test_data/dwi_rot/dwi_rot.par", "test_data/dwi_rot/dwi_rot.bvec"),
    ]
    for par_file, goal_bvec_file in test_list:
        goal_bvecs = np.genfromtxt(goal_bvec_file)
        print(par_file, goal_bvec_file)
        rotated_bvecs = rotate_bvecs(bvecs_from_scanner, par_file)
        assert_almost_equal(rotated_bvecs, goal_bvecs, 5)

    # fail test
    par_file, goal_bvec_file = ("test_data/dwi/dwi.par", "test_data/dwi_rot/dwi_rot.bvec")
    goal_bvecs = np.genfromtxt(goal_bvec_file)
    rotated_bvecs = rotate_bvecs(bvecs_from_scanner, par_file)
    diff = np.abs((rotated_bvecs - goal_bvecs).sum())
    assert (diff > 0.1)


####
"""
adapten from https://github.com/nipy/nibabel/blob/master/nibabel/parrec.py
to work with msec in par file

"""

import numpy as np
import nibabel as nb

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


def _process_gen_dict(gen_dict):
    # Process `gen_dict` key, values into `general_info`
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
