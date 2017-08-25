"""
 OCCAM

 Copyright (c) 2017, SRI International

  All rights reserved.

 Redistribution and use in source and binary forms, with or without
 modification, are permitted provided that the following conditions are met:

 * Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

 * Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

 * Neither the name of SRI International nor the names of its contributors may
   be used to endorse or promote products derived from this software without
   specific prior written permission.

 THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
 FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
 OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import os
import sys

import yaml

from .constants import PATH_REPO_DIR
from .constants import PATH_RECIPE_FILE
from .constants import PATH_CONTENTS_FILE
from .constants import PATH_TMP_CONTENTS_FILE
from .constants import PATH_BUILD_BASE_DIR

from .package import Package
from .logconfig import logConfig

from .image import get_package_image_name
from .image import get_subpkg_hash
from .image import build_docker_image
from .image import get_base_image_name

logger = logConfig(__name__)

class Repository(object):
    def __init__(self, args):
        self.args = args

    def build_dependency_graph(self, target_pkg_name):
        graph = {}
        pkg_map = {}
        todo = [target_pkg_name]
        pkg_map[target_pkg_name] = self.get_package_obj(target_pkg_name)

        while todo:
            pkg_name = todo.pop()
            pkg = pkg_map[pkg_name]
            graph[pkg_name] = []
            pkg_deps = pkg.get_build_dependencies()
            if pkg_deps:
                for dep_pkg_name in pkg_deps.keys():
                    deps_subpkgs = pkg_deps[dep_pkg_name]
                    if dep_pkg_name in pkg_map:
                        dep_pkg = pkg_map[dep_pkg_name]
                    else:
                        dep_pkg = self.get_package_obj(dep_pkg_name)
                        pkg_map[dep_pkg_name] = dep_pkg

                    # Check dep subpackages
                    rebuild_dep = False
                    for dep_sub in deps_subpkgs:
                        img_name = get_package_image_name(dep_pkg_name, dep_sub)
                        subpackages_contents = dep_pkg.get_subpackages_contents()
                        contents_file_hash = subpackages_contents[dep_sub]['checksum']
                        real_img_hash = get_subpkg_hash(img_name)
                        if contents_file_hash != real_img_hash:
                            rebuild_dep = True

                    # Add dependency to graph if needed
                    if rebuild_dep:
                        if not dep_pkg_name in todo:
                            todo.append(dep_pkg_name)
                        graph[pkg_name].append(dep_pkg_name)
        return (graph, pkg_map)

    def remove_dependency_graph_node(self, pkg_id, dependency_graph):
        return {k: filter(lambda a: a != pkg_id, v) for k, v in dependency_graph.items()}

    def resolve_build_dependencies(self, target_pkg_name):
        (dependency_graph, pkg_map) = self.build_dependency_graph(target_pkg_name)
        dependency_pkg_lst = []
        nb_deps = len(dependency_graph.keys())
        while nb_deps > 0:
            for pkg_id, pkg_deps in dependency_graph.items():
                if not pkg_deps:
                    dependency_pkg_lst.append(pkg_map[pkg_id])
                    del dependency_graph[pkg_id]
                    dependency_graph = self.remove_dependency_graph_node(pkg_id, dependency_graph)
            new_nb_deps = len(dependency_graph.keys())
            if nb_deps == new_nb_deps:
                logger.error('Could not resolve dependencies. There may be a directed cycle in the graph.')
                sys.exit(1)
            else:
                nb_deps = new_nb_deps
        return dependency_pkg_lst

    def get_package_obj(self, pkg_name):
        pkg_path = os.path.join(PATH_REPO_DIR, pkg_name)
        recipe_file_path = os.path.join(pkg_path, PATH_RECIPE_FILE)
        contents_file_path = os.path.join(pkg_path, PATH_CONTENTS_FILE)
        if os.path.isfile(recipe_file_path):
            recipe_file_obj = open(recipe_file_path, 'r')
            recipe_file_contents = recipe_file_obj.read()
            if os.path.isfile(contents_file_path):
                contents_file_obj = open(contents_file_path, 'r')
                contents_file_contents = contents_file_obj.read()
            else:
                contents_file_contents = None
            return Package(pkg_name, recipe_file_contents, contents_file_contents, self.args)
        else:
            logger.error('The package %s was not found in the local repository. Aborting.', pkg_name)
            sys.exit(1)

    def build_images(self, pkg_obj, no_cache, commit_mode, tolerant):
        pkg_name = pkg_obj.get_package_name()
        pkg_path = os.path.join(PATH_REPO_DIR, pkg_name)
        # Build package
        logger.info('Building package %s', pkg_name)
        img_name = get_package_image_name(pkg_name)
        df_filename = 'Dockerfile-'+img_name
        df_file = open(os.path.join(pkg_path, df_filename), 'w')
        pkg_obj.write_build_dockerfile(df_file)
        build_docker_image(img_name, pkg_path, no_cache, df_filename, True)

        # Build subpackages
        is_err = False
        is_change = False
        subpackages_contents = pkg_obj.get_subpackages_contents()
        for subpackage_name in subpackages_contents:
            logger.info('Building subpackage %s from package %s', subpackage_name, pkg_name)
            img_name = get_package_image_name(pkg_name, subpackage_name)
            subpkg_contents = subpackages_contents[subpackage_name]['files']
            df_filename = 'Dockerfile-'+img_name
            df_file = open(os.path.join(pkg_path, df_filename), 'w')

            # Writing subpackage contents to file
            tmp_contents_path = os.path.join(pkg_path, PATH_TMP_CONTENTS_FILE)
            tmp_contents_file = open(tmp_contents_path, "w")
            tmp_contents_file.write("%s\n" % '\n'.join(subpkg_contents))
            tmp_contents_file.close()

            # Build subpackage
            is_subpkg = False
            if subpkg_contents:
                is_subpkg = True
            pkg_obj.write_subpackage_dockerfile(df_file, is_subpkg, subpackage_name)
            build_docker_image(img_name, pkg_path, no_cache, df_filename, True)

            # Delete tmp files
            os.remove(tmp_contents_path)

            # Check hashes
            contents_file_hash = subpackages_contents[subpackage_name]['checksum']
            real_img_hash = get_subpkg_hash(img_name)
            if contents_file_hash != real_img_hash:
                if not commit_mode:
                    if not tolerant:
                        is_err = True
                        squark = logger.error
                    else:
                        squark = logger.info
                    squark('Checksum for built subpackage does not match expected checksum.')
                    squark('\n\tBuilt: %s\n\tExpected: %s', real_img_hash, contents_file_hash)
                else:
                    is_change = True
                    logger.info('Commiting checksum change in subpackage.')
                    logger.info('\n\tOld: %s\n\tNew: %s', contents_file_hash, real_img_hash)
                    subpackages_contents[subpackage_name]['checksum'] = real_img_hash

        if is_err:
            logger.error('There was an error building the subpackages. Stopping.')
            sys.exit(1)

        if is_change:
            logger.info('Writing checksum changes in contents file.')
            contents_file_path = os.path.join(pkg_path, PATH_CONTENTS_FILE)
            contents_file = open(contents_file_path, 'w')
            yaml.dump(subpackages_contents, contents_file, default_flow_style=False, indent=4)
            contents_file.close()


    def build_base(self, no_cache):
        logger.info('Building build base')
        df_path = os.path.join(PATH_BUILD_BASE_DIR, 'Dockerfile')
        if os.path.isfile(df_path):
            img_name = get_base_image_name()
            build_docker_image(img_name, PATH_BUILD_BASE_DIR, no_cache, 'Dockerfile', False)
        else:
            logger.error('No Dockerfile found into the %s directory. Aborting.', PATH_BUILD_BASE_DIR)
            sys.exit(1)
