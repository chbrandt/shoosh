"""
Docker handlers
"""
import sh
import json

from io import StringIO
from sh import docker

from . import _log as log

SHELL_COMMAND="bash --login -c"

def bake(container):
    """
    Return a Bash login shell from "inside" container 'name'

    "Inside" means it will exec whatever (wrapped) command from inside the
    (docker) container in a Bash login shell.
    """
    exec_ = "exec -t {container!s} {SHELL_COMMAND!s}"

    if container not in list_containers():
        # TODO: together with an option "autorun", start/run container if not yet.
        raise ValueError
    sh_ = docker.bake(exec_.format(container=container).split())
    return sh_


def containers() -> list:
    """
    Return list of container (names) instanciated
    """
    from sh import awk, tail
    buf = StringIO()
    try:
        tail(awk(docker('ps','-a'), '{print $NF}'), '-n+2', _out=buf)
    except Exception as err:
        log.error(err)

    containers = buf.getvalue().split()
    return containers

list_containers = containers


def volumes(container:str) -> list:
    """
    Return list of 'container' volumes (host,cont)
    """
    buf = StringIO()
    docker('inspect', '-f', "'{{json .Mounts}}'", container, _out=buf)
    res = buf.getvalue().strip()
    vols_list = json.loads(res[1:-1])
    # vols = {d['Source']:d['Destination'] for d in vols_list}
    vols = [(d['Source'],d['Destination']) for d in vols_list]
    return vols

list_volumes = volumes


def run(image:str, name:str, volumes:list=None, ports:list=None) -> bool:
    """
    Run a container, from given 'image', binding 'volumes' and 'ports'
    """
    if name in containers():
        log.error(f"Container '{name}' already exists")
        return False

    if volumes and len(volumes) == 2:
        if isinstance(volumes[0], str):
            assert isinstance(volumes[1], str)
            volumes = [volumes]
        else:
            assert isinstance(volumes[0], (tuple,list))
            assert isinstance(volumes[1], (tuple,list))
    if ports is not None:
        log.warning("'ports' argument is not implemented yet...moving on")
        pass

    vols = [ f'{h},{c}' for h,c in volumes ]
    docker('run','-v', *vols)
    return True


def start(container:str) -> bool:
    """
    (Re)start a container
    """
    from sh import docker

    if container in containers():
        docker('start', container)
        return True
    else:
        log.error(f"Container '{container}' is not available.")
        return False
