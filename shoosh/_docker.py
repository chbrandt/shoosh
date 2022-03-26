"""
Docker handlers
"""
import json
from io import StringIO
from sh import docker
from . import _log as log

SHELL_COMMAND="bash --login -c"

def containers() -> list:
    """
    Return list of container (names) instanciated
    """
    from sh import awk, tail
    buf = StringIO()

    _exec(tail,
        _exec(awk,
            _exec(docker, 'ps','-a'),
        '{print $NF}'),
    '-n+2', _out=buf)

    containers = buf.getvalue().split()
    return containers

list_containers = containers


def volumes(container:str) -> list:
    """
    Return list of 'container' volumes (host,cont)
    """
    buf = StringIO()

    _exec(
        docker, 'inspect', '-f', "'{{json .Mounts}}'", container, _out=buf
    )

    res = buf.getvalue().strip()
    vols_list = json.loads(res[1:-1])

    # vols = {d['Source']:d['Destination'] for d in vols_list}
    vols = [(d['Source'],d['Destination']) for d in vols_list]
    return vols

list_volumes = volumes


def bake(container):
    """
    Return a 'sh' instance running inside 'container'
    """
    exec_ = "exec -t {container!s} " + SHELL_COMMAND

    if container not in containers():
        log.error(f"Container '{container}' not available.")
        return None

    sh_ = docker.bake(exec_.format(container=container).split())
    return sh_


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

    maps = []
    if volumes:
        vols = [ f'{h},{c}' for h,c in volumes ]
        maps = ['-v'] + vols

    return _exec(docker, 'run', '-dt', '--name', name, *maps, image)


def start(container:str) -> bool:
    """
    (Re)start a container
    """
    if container not in containers():
        log.error(f"Container '{container}' is not available.")
        return None

    return _exec(docker, 'start', container)


def _exec(foo, *args, **kwargs):
    try:
        return foo(*args, **kwargs)
    except Exception as err:
        log.error(err)
        return None
