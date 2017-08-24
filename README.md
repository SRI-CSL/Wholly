# Wholly!

## Overview

This project, *Wholly!*, provides a Python tool that can build clean packages in a traceable way from open-source code. We make use of Docker containers to provide a minimal and controlled build environment, clear and meaningful build "recipes" to describe precisely the dependencies and the build invocations, and fine-grained sub-packaging to release lightweight and usable images.

To achieve that, *Wholly!* provides the orchestration to build a package using a **recipe** that we try to keep as simple as possible. All the available recipies are to be stored in a local repository, or working directory.

We provide such an example working directory that is suitable to build packages for the `x86_64` architecture. Steps to use it are described below.

## Usage

### Requirements

- Python 2.7.x with `pip`
- Docker CE >= 17.05: https://www.docker.com/community-edition

### Fetch the project

In order to build packages with Wholly, you need to clone both the tool and a working directory. Let us assume that you want to clone them side by side:

```
git clone https://github.com/SRI-CSL/Wholly.git
git clone https://github.com/SRI-CSL/WhollyRecipes.git
```

### Install PyYAML

PyYAML is a dependency for *Wholly!*. Install it by executing:

```
pip install pyyaml
```

### Usage

We need to execute *Wholly!* from the working directory:
```
cd WhollyRecipes
```

Make sure that the Docker deamon is running by executing the Docker application. You can now build any package present into the working directory:

```
../Wholly/wholly.py build sqlite-3.18
```
This will build `sqlite-3.18` along with its dependencies. In particular, it will generate sub-packages for `sqlite-3.18`, in the form of Docker images:

```
$ docker images | grep wholly-sqlite-3.18-
wholly-sqlite-3.18-libs       latest        1.34MB
wholly-sqlite-3.18-headers    latest        528kB
wholly-sqlite-3.18-bin        latest        1.24MB
```

### Useful options

- The `--no-cache` flag forces Docker to rebuild the packages.
- The `--nb-cores` flag is useful for some packages that support concurrent builds. The command `../Wholly/wholly.py build libcxx-4.0 --nb-cores 4`, for example, will build the package `libcxx-4.0` using 4 cores. Of course, the number of cores that you specify cannot be greater than the number of cores that you allocated to your Docker machine.



### Debugging

Wholly can show various levels of output to aid with debugging.
To show this output set the `WHOLLY_LOG_LEVEL` environment
variable to one of the following levels:

 * `ERROR`
 * `WARNING`
 * `INFO`
 * `DEBUG`

For example:
```
    export WHOLLY_LOG_LEVEL=DEBUG
```
Output will be directed to the standard error stream, unless you specify the
path of a logfile via the `WHOLLY_LOG_FILE` environment variable.

For example:
```
    export WHOLLY_LOG_FILE=/tmp/wholly.log
```

When the level is set to `DEBUG` the messages contain more locality information.


###  Checksum Mismatches

If one is building a package and one discovers that the checksums do not match, you can either:

- Use the `--commit-all` command switch, which will replace the old checksums by the new ones.

- Use the `ignore-checksums` command switch, which will simply igmore the mismatches (while still reporting them).
