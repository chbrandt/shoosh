# shoosh
Wrapper for sh to run Shell commands inside Docker container and handle volume mappings seamlessly.

## How to

### 1: Instantiate a container
First step is to instantiate the (Docker) container we are going to use next.
(You'll use whatever method/interface you're used to do it; the lib is _not_
meant to manage the containers lifecycle.)

For example, let's run a simple [alpine](https://hub.docker.com/_/alpine) container mapping local `test/` directory to `/some/path` inside the container:
```bash
$ docker run -dt \
        --name some_container \
        -v /tmp/test:/some/path \
        debian
```

### 2: Create a handle to container
Then, we create a handle to the container whit the volume(s) set:
```python
>>> import shoosh
>>> sh = shoosh.init('some_container')
```

### 3: And execute a command through the handle
By default, whenever you cite the (host) volume, it translate to the internal path:
```python
>>> echo = sh.wrap('echo')
>>> echo("Internal path:", '/tmp/test')
Internal path: /some/path
```

## Rationale
The typical use of (Docker) containers is to spin-up a container containing
the software packages we need to accomplish a given task, process the data
we aim to, and eventually get the results back to the host system.

When we run (Docker) containers, though, the filesystem structure inside the
container is completely detached from that of the host system.
The way to exchange data files between host and container is through container mounting points -- or _volumes_.

In practice, it means that the _paths_ we see inside a container -- where our
data is sitting -- is different than that of the host system -- where the very
same data files are stored, and being shared through volumes to the container.

Consider the following scenario:
- For some reason we use a [osgeo/gdal] container to process geographical data;
- The data in our host system is stored under `/home/user/data/some_project`;
- When we instantiate the [osgeo/gdal] image as `some_gdal` container, we mount-bind that path to container's `/data/geo`;
- Suppose all we want to do it to [convert our data files from GeoTiff to Cloud Optimized GeoTiff(https://gdal.org/drivers/raster/cog.html):
  ```bash
  $ gdal_translate /data/geo/raster.tif /data/geo/raster_cog.tif -of COG
  ```

Everything works very well if the interaction with the container is decoupled
from the host system, _i.e._ if we are _executing_ the commands _inside_ the
container. But if there is a need for _requesting_ the execution of a command
_from_ the host system _inside_ the container, one should be aware of the
different paths resulting from a host-container volumes binding.

The demand for _requesting_ processing tasks (from the host system) to execute
inside a container have different motivations, clearly; It can be a personal
demand of having the host system software set clean and the convenience of not
getting inside the container every time a simple, atomic task has to be performed.
But it can also be part of a more complex software application running on the
host system -- like a data processing pipeline -- where different components
demand different third-party software tools (available through containers).

### Motivation
In my case, the reason I wrote this software, is I use Python to transform
planetary (Mars) geo-located data in different ways using either OSGEO's GDAL
as well as USGS's ISIS software packages in a couple of cloud computing projects (GMAP, NEANIAS).
I had to find a way, for my own convenience, to merge data visualization, metadata
selection, download, cleaning, map-projection, formatting, etc., from the host
system and on containers seamlessly through Python.


## Application (value)
This (Python) library _primary feature_ is the execution of Shell commands inside
(Docker) containers _and_ the correct _re-mapping of paths on the fly_.
It does _also_ provides a seamless interface to execute Shell commands in the
current environment, re-mapping of paths is not necessary in this case but it
allow you to move your code from a "host-container" scenario to "container-only"
-- in a cloud infrastructure -- seamlessly.

All this _seamlessly_ feature is possible because of the [sh](pypi.org/sh) package.
