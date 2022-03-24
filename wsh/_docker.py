import json
from io import StringIO
from sh import docker, awk, tail

from . import _log as log


def bake(container):
    """
    Return a Bash login shell from "inside" container 'name'

    "Inside" means it will exec whatever (wrapped) command from inside the
    (docker) container in a Bash login shell.
    """
    exec_ = "exec -t {container!s} bash --login -c"
    if container not in list_containers():
        # TODO: together with an option "autorun", start/run container if not yet.
        raise ValueError
    sh_ = docker.bake(exec_.format(container=container).split())
    return sh_


def containers():
    """
    Return list of container (names) instanciated
    """
    buf = StringIO()
    try:
        tail(awk(docker('ps','-a'), '{print $NF}'), '-n+2', _out=buf)
    except Exception as err:
        log.error(err)

    containers = buf.getvalue().split()
    return containers

list_containers = containers


def restart(name):
    """
    Re/Start a container
    """
    if name in containers():
        docker('start',name)
        return True
    else:
        log.warning(f"No container '{name}' instantiated. Nothing to restart.")
        return False

container_restart = restart


def volumes(container:str) -> list:
    """
    Return container volume pairs
    """
    buf = StringIO()
    docker('inspect', '-f', "'{{json .Mounts}}'", container, _out=buf)
    res = buf.getvalue().strip()
    vols_list = json.loads(res[1:-1])
    # vols = {d['Source']:d['Destination'] for d in vols_list}
    vols = [(d['Source'],d['Destination']) for d in vols_list]
    return vols

container_volumes = volumes
