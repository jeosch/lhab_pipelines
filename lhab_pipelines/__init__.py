import os

__package__ = "lhab_pipelines"
__all__ = ["nii_conversion"]

dir_path = os.path.dirname(os.path.realpath(__file__))
with open(os.path.join(dir_path, "../version")) as fi:
    __version__ = fi.read().strip()
