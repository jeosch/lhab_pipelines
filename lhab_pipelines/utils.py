
import os

# docker stuff
def get_docker_container_id():
    cmd = "cat /proc/self/cgroup | grep 'cpu:/' | sed 's/\([0-9]\):cpu:\/docker\///g'"
    docker_container_id = os.popen(cmd).read()
    return docker_container_id