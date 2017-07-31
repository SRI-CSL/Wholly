# Wholly!

## Overview

This project, *Wholly!*, provides a Python tool that can build clean packages in a traceable way from open-source code. We make use of Docker containers to provide a minimal and controlled build environment, clear and meaningful build "recipes" to describe precisely the dependencies and the build invocations, and fine-grained sub-packaging to release lightweight and usable images.

To achieve that, *Wholly!* provides the orchestration to build a package using a **recipe** that we try to keep as simple as possible. All the available recipies are to be stored in a local repository, or working directory.

We provide such an example working directory that is suitable to build packages for the `x86_64` architecture. Steps to use it are described below.

## Usage

### Requirements

- Python 2.7.x
- Docker CE >= 17.05: https://www.docker.com/community-edition

### Fetch the project

In order to build packages with Wholly, you need to clone both the tool and a working directory. Let us assume that you want to clone them side by side:

```
git clone git@github.com:SRI-CSL/Wholly.git
git clone git@github.com:SRI-CSL/WhollyRecipes.git
```

### Usage

We need to execute *Wholly!* from the working directory:
```
cd WhollyRecipes
```

You can now build any package present into the working directory:

```
./../Wholly/wholly.py build sqlite-3.18
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
- The `--nb-cores` flag is useful for some packages that support concurrent builds. The command `./../Wholly/wholly.py build libcxx-4.0 --nb-cores 4`, for example, will build the package `libcxx-4.0` using 4 cores. Of course, the number of cores that you specify cannot be greater than the number of cores that you allocated to your Docker machine.
