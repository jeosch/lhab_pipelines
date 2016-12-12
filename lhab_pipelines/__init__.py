from .utils import check_docker_container_version

__package__ = "lhab_pipelines"
__all__ = ["nii_conversion"]

check_docker_container_version("fliem/lhab_docker:v0.7")