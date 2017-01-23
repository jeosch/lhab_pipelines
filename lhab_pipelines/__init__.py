from .utils import check_docker_container_version
import os

__package__ = "lhab_pipelines"
__all__ = ["nii_conversion"]

dir_path = os.path.dirname(os.path.realpath(__file__))
with open(os.path.join(dir_path, "../version")) as fi:
    __version__ = fi.read().strip()

check_docker_container_version("fliem/lhab_docker:v0.7")
