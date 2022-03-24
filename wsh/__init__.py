"""
Wrapper for SH
"""
import sh

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions

from . import _log as log
from ._sh import Sh as Wsh

def init_shell(container:str, mappings=None, name:str=None):
    """
    Return a shell for 'container'
    """
    sh = Wsh(name)
    sh.set_docker(container, mappings, inspect=True)
    return sh
