"""
Wrapper for SH
"""
from ._version import get_versions
__version__ = get_versions()['version']
del get_versions

from . import _log as log

from ._sh import Sh as Wsh

try:
    from . import _docker as docker
except:
    docker = None

def get_handle(container_name:str):
    """
    Return a shell for 'container_name'
    """
    vols = docker.container_volumes(container_name)
    sh = Wsh()
    sh.set_docker(container_name, vols)
    return sh
