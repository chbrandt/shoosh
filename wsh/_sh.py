from . import log

try:
    from . import _docker as docker
except:
    docker = None


KWARGS_SEP = '='


class Sh(object):
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
    def log(res):
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
            self.log("Docker not found. Do you have it installed?")

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
    from os.path import exists,abspath

    if maps and exists(value):
        _abs = abspath(value)
        for _host, _cont in maps:
            _val = _abs.replace(_host, _cont)
            if _val != _abs:
                return _val

    return value


def _map_kwarg_d(key, value, maps, sep='='):
    _val = _map_arg(value, [maps]) if maps else value
    return f"{key}{sep}{_val}"


def _map_kwarg_t(key, value, maps, sep='='):
    _val = _map_arg(value, maps) if maps else value
    return f"{key}{sep}{_val}"


def _set_sh():
    """
    Return a Bash login shell
    """
    from sh import bash
    return bash.bake('--login -c'.split())


# def _map_args(args, map_paths):
#     """
#     Translate 'args' according to 'map_paths'
#
#     'args' is like:
#     ```
#     ['dummy-arg', '/Volumes/at_host/bla.txt']
#     ```
#     And 'map_paths' (given at 'Sh.set_docker()') is like:
#     ```
#     { 'infile': ('/Volumes/at_host', '/mnt/at_container') }
#     ```.
#     """
#     import re
#
#     log.debug(args)
#     log.debug(map_paths)
#
#     map_tuples = map_paths.values() if isinstance(map_paths, dict) else map_paths
#     assert False
#     _args = []
#     for val in args:
#         for _host, _cont in map_tuples:
#             # use str.replace to substitute wherever '_host' is in the string
#             _val = val.replace(_host, _cont)
#             # re.sub to substitute only when '_host' strats ('^') the string
#             # _val = re.sub(f"^{_host}", _cont, val)
#             if _val != val:
#                 break
#         _args.append(_val)
#
#     return _args
#
#
# def _map_kwargs(kwargs, map_paths):
#     """
#     Translate 'kwargs' values according to 'map_paths' mappings
#
#     'kwargs' is something like:
#     ```
#     { 'infile' : '/Volumes/at_host/bla.txt' }
#     ```.
#
#     And 'map_paths' (given at 'Sh.set_docker()') is like:
#     # ```
#     # TODO: implement this format!
#     # { '/Volumes/at_host' : '/mnt/at_container' }
#     # ```
#     # or
#     ```
#     { 'infile': ('/Volumes/at_host', '/mnt/at_container') }
#     ```.
#     The second form is used only when you want to restrict such mapping/translation
#     to a specific command-line argument
#     """
#     log.debug(kwargs)
#     log.debug(map_paths)
#
#     map_tuples = map_paths.values() if isinstance(map_paths, dict) else map_paths
#
#     _kw = {}
#     for key, val in kwargs.items():
#         for _host, _cont in map_tuples:
#             _val = val.replace(_host, _cont)
#             if _val != val:
#                 break
#         _kw[key] = _val
#
#     return _kw
#
