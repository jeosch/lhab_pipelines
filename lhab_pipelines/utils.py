
import os

# docker stuff
def get_docker_container_name():
    docker_container_name = os.getenv("DOCKER_IMAGE")
    return docker_container_name
