import os
import sys
import logging
import image

import constants as cst
from package import Package

class Repository:
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
                for dep_pkg_name in pkg_deps:
                    if dep_pkg_name in pkg_map:
                        dep_pkg = pkg_map[dep_pkg_name]
                    else:
                        dep_pkg = self.get_package_obj(dep_pkg_name)
                        pkg_map[dep_pkg_name] = dep_pkg
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
        while (nb_deps > 0):
            for pkg_id, pkg_deps in dependency_graph.items():
                if not pkg_deps:
                    dependency_pkg_lst.append(pkg_map[pkg_id])
                    del dependency_graph[pkg_id]
                    dependency_graph = self.remove_dependency_graph_node(pkg_id, dependency_graph)
            new_nb_deps = len(dependency_graph.keys())
            if nb_deps == new_nb_deps:
                logging.error('Could not resolve dependencies. There may be a directed cycle in the graph.')
                sys.exit(1)
            else:
                nb_deps = new_nb_deps
        return dependency_pkg_lst

    def get_package_obj(self, pkg_name):
        pkg_path = os.path.join(cst.PATH_REPO_DIR, pkg_name)
        recipe_file_path = os.path.join(pkg_path, cst.PATH_RECIPE_FILE)
        contents_file_path = os.path.join(pkg_path, cst.PATH_CONTENTS_FILE)
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
            logging.error('The package '+pkg_name+' was not found in the local repository. Aborting.')
            sys.exit(1)

    def build_images(self, pkg_obj, no_cache):
        pkg_name = pkg_obj.get_package_name()
        pkg_path = os.path.join(cst.PATH_REPO_DIR, pkg_name)
        # Build package
        logging.info('Building package '+pkg_name)
        img_name = image.get_package_image_name(pkg_name)
        df_filename = 'Dockerfile-'+img_name
        df_file = open(os.path.join(pkg_path, df_filename), 'w')
        pkg_obj.write_build_dockerfile(df_file)
        image.build_docker_image(img_name, pkg_path, no_cache, df_filename, True)

        # Build subpackages
        subpackages_contents = pkg_obj.get_subpackages_contents()
        for subpackage_name in subpackages_contents:
            logging.info('Building subpackage '+subpackage_name+' from package '+pkg_name)
            img_name = image.get_package_image_name(pkg_name, subpackage_name)
            subpkg_contents = subpackages_contents[subpackage_name]
            df_filename = 'Dockerfile-'+img_name
            df_file = open(os.path.join(pkg_path, df_filename), 'w')

            # Writing subpackage contents to file
            tmp_contents_path = os.path.join(pkg_path, cst.PATH_TMP_CONTENTS_FILE)
            tmp_contents_file = open(tmp_contents_path, "w")
            tmp_contents_file.write("%s\n" % '\n'.join(subpkg_contents))
            tmp_contents_file.close()

            # Build subpackage
            pkg_obj.write_subpackage_dockerfile(df_file, subpkg_contents, subpackage_name)
            image.build_docker_image(img_name, pkg_path, no_cache, df_filename, True)

            # Delete tmp contents file
            os.remove(tmp_contents_path)

    def build_base(self, no_cache):
        logging.info('Building build base')
        df_path = os.path.join(cst.PATH_BUILD_BASE_DIR, 'Dockerfile')
        if os.path.isfile(df_path):
            img_name = image.get_base_image_name()
            image.build_docker_image(img_name, cst.PATH_BUILD_BASE_DIR, no_cache, 'Dockerfile', False)
        else:
            logging.error('No Dockerfile found into the '+cst.PATH_BUILD_BASE_DIR+' directory. Aborting.')
            sys.exit(1)
