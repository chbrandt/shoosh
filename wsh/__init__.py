"""
Wrapper for SH
"""
# import sh
# isissh = sh(_long_prefix="")

from . import _log as log

from ._sh import Sh as Wsh


from ._version import get_versions
__version__ = get_versions()['version']
del get_versions
