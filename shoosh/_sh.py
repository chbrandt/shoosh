from . import log

try:
    from . import _docker as docker
except:
    docker = None


KWARGS_SEP = '='


class Shoosh(object):
    """
    Class meant to abstract the underlying Shell/OS layer

    It is similar to the package 'sh' (https://pypi.org/project/sh/) in the
    sense that it "wraps" command-line/shell commands to work seemlessly from
    inside Python.
    Different from pure 'sh' (which this class is based on),
    this class necessarily adds a routing layer: instead of doing `sh.ls('-l')`
    as you would with 'sh', here you have to do `ls = sh.wrap('ls'); ls('-l')`.
    Which *is similar* to 'sh.bare' method, but here is mandatory.

    There are three reasons that justify it:
    * commands are *always* run in a bash login shell,
    * docker containers can be set to seemlessly run commands,
    * a logging handler is set to *always* log the wrapped commands

    In case a (docker) container is used, and volumes are being used for I/O,
    this wrapper also *translates* host URL to corresponding ones inside docker.
    """
    _sh = None
    _maps = None
    _name = None
    _kwargs_sep = None

    def __init__(self, name:str=None, kwargs_sep:str=KWARGS_SEP):
        self._name = name
        self._kwargs_sep = kwargs_sep
        self.reset()

    def __call__(self, command):
        log.debug(command)
        return self._sh(command)

    def reset(self):
        """
        Simply start a brand new shell.
        """
        _sh = _set_sh()
        log.debug(_sh)
        self._sh = _sh
        self._maps = None

    @staticmethod
    def _log(res):
        log.debug("Exit code: "+str(res and res.exit_code))

    def set_docker(self, container, mappings=None, inspect=False):
        """
        Set running 'container' to handle exec/commands

        Input:
            container: string
                Name of a running container
            mappings: list, dictionary
                Either a list/tuple mapping host to container paths,
                `` ('path_in_host', 'path_in_container') ``
                or a dictionary where keys are labels/args and values the tuples:
                `` { 'arg': ('path_in_host', 'path_in_container') } ``
        """
        if docker:
            assert container in docker.list_containers()
            self._sh = docker.bake(container)
            if inspect and not mappings:
                mappings = docker.volumes(container)
            assert type(mappings) in (list,tuple,dict)
            if isinstance(mappings, list):
                mappings = tuple(mappings)
            self._maps = {type(mappings): mappings}
        else:
            self._log("Docker not found. Do you have it installed?")

    def wrap(self, exec):
        """
        Return a callable wrapping command 'exec'

        This callable (really just a closure around Sh/Bash) accepts *any*
        argument(s) or kw-argument(s) you feel like running 'exec' with.

        Input:
            * exec : str
                Command name to wrap (e.g, "echo")
        """
        if isinstance(exec, str):
            exec = [exec]

        def _sh(*args, **kwargs):
            """
            Run and return result of 'exec' in 'sh_local' with argument 'args/kwargs'
            """
            _maps_t = self._maps.get(tuple, None)
            v = [ _map_arg(v, _maps_t) for v in args ]
            _maps_d = self._maps.get(dict, None)
            if _maps_d:
                kv = [ _map_kwarg_d(k, v, _maps_d.get(k), self._kwargs_sep)
                        for k,v in kwargs.items() ]
            else:
                kv = [ _map_kwarg_t(k, v, _maps_t, self._kwargs_sep)
                        for k,v in kwargs.items() ]

            # 'comm' is effectively the full/command-line to run
            comm = ' '.join(exec+v+kv)
            log.debug(comm)
            return self(comm)

        return _sh

    @property
    def mappings(self):
        """
        Return list of volumes/mappings currently set
        """
        return self._maps


def _map_arg(value, maps):
    """
    Return mapped 'value' if mapping found in 'maps'

    Input:
        value: str
            Path (string) in the host system
            Ex: '/host/path/something'
        maps: list
            List of length-2 tuples [('/host/path','/container/path')]

    Output:
        Mapped value. Ex: '/container/path/something'
    """
    from os.path import exists,abspath

    if maps and exists(value):
        _abs = abspath(value)
        for _host, _cont in maps:
            _val = _abs.replace(_host, _cont)
            if _val != _abs:
                return _val

    return value


def _map_kwarg_t(key, value, maps, sep):
    """
    Return keyword value mapped using separator 'sep'
    """
    _val = _map_arg(value, maps)
    return f"{key}{sep}{_val}"


def _map_kwarg_d(key, value, maps, sep):
    """
    Return keyword value mapped using separator 'sep'
    """
    _maps = maps and [maps]
    return _map_kwarg_t(key, value, _maps, sep)


def _set_sh():
    """
    Return a Bash login shell
    """
    from sh import bash
    return bash.bake('--login -c'.split())
