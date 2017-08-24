import os
import sys
import image

import yaml

import constants as cst

from package import Package

from logconfig import logConfig

logger = logConfig(__name__)

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
                        img_name = image.get_package_image_name(dep_pkg_name, dep_sub)
                        subpackages_contents = dep_pkg.get_subpackages_contents()
                        contents_file_hash = subpackages_contents[dep_sub]['checksum']
                        real_img_hash = image.get_subpkg_hash(img_name)
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
        while (nb_deps > 0):
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
            logger.error('The package {0} was not found in the local repository. Aborting.'.format(pkg_name))
            sys.exit(1)

    def build_images(self, pkg_obj, no_cache, commit_mode):
        pkg_name = pkg_obj.get_package_name()
        pkg_path = os.path.join(cst.PATH_REPO_DIR, pkg_name)
        # Build package
        logger.info('Building package {0}'.format(pkg_name))
        img_name = image.get_package_image_name(pkg_name)
        df_filename = 'Dockerfile-'+img_name
        df_file = open(os.path.join(pkg_path, df_filename), 'w')
        pkg_obj.write_build_dockerfile(df_file)
        image.build_docker_image(img_name, pkg_path, no_cache, df_filename, True)

        # Build subpackages
        is_err = False
        is_change = False
        subpackages_contents = pkg_obj.get_subpackages_contents()
        for subpackage_name in subpackages_contents:
            logger.info('Building subpackage {0} from package {1}'.format(subpackage_name, pkg_name))
            img_name = image.get_package_image_name(pkg_name, subpackage_name)
            subpkg_contents = subpackages_contents[subpackage_name]['files']
            df_filename = 'Dockerfile-'+img_name
            df_file = open(os.path.join(pkg_path, df_filename), 'w')

            # Writing subpackage contents to file
            tmp_contents_path = os.path.join(pkg_path, cst.PATH_TMP_CONTENTS_FILE)
            tmp_contents_file = open(tmp_contents_path, "w")
            tmp_contents_file.write("%s\n" % '\n'.join(subpkg_contents))
            tmp_contents_file.close()

            # Build subpackage
            is_subpkg = False
            if subpkg_contents:
                is_subpkg = True
            pkg_obj.write_subpackage_dockerfile(df_file, is_subpkg, subpackage_name)
            image.build_docker_image(img_name, pkg_path, no_cache, df_filename, True)

            # Delete tmp files
            os.remove(tmp_contents_path)

            # Check hashes
            contents_file_hash = subpackages_contents[subpackage_name]['checksum']
            real_img_hash = image.get_subpkg_hash(img_name)
            if contents_file_hash != real_img_hash:
                if not commit_mode:
                    is_err = True
                    logger.error('Checksum for built subpackage does not match expected checksum.')
                    logger.error('\n\tBuilt: {0}\n\tExpected: {1}'.format(real_img_hash, contents_file_hash))
                else:
                    is_change = True
                    logger.info('Commiting checksum change in subpackage.')
                    logger.info('\n\tOld: {0}\n\tNew: {1}'.format(contents_file_hash, real_img_hash))
                    subpackages_contents[subpackage_name]['checksum'] = real_img_hash

        if is_err:
            logger.error('There was an error building the subpackages. Stopping.')
            sys.exit(1)

        if is_change:
            logger.info('Writing checksum changes in contents file.')
            contents_file_path = os.path.join(pkg_path, cst.PATH_CONTENTS_FILE)
            contents_file = open(contents_file_path, 'w')
            contents_dump = yaml.dump(subpackages_contents, contents_file, default_flow_style=False, indent=4)
            contents_file.close()


    def build_base(self, no_cache):
        logger.info('Building build base')
        df_path = os.path.join(cst.PATH_BUILD_BASE_DIR, 'Dockerfile')
        if os.path.isfile(df_path):
            img_name = image.get_base_image_name()
            image.build_docker_image(img_name, cst.PATH_BUILD_BASE_DIR, no_cache, 'Dockerfile', False)
        else:
            logger.error('No Dockerfile found into the {0} directory. Aborting.'.format(cst.PATH_BUILD_BASE_DIR))
            sys.exit(1)
