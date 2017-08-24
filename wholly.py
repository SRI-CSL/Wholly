#!/usr/bin/env python
import sys
import os
import shutil

import constants as cst
from repository import Repository
import parser
from logconfig import logConfig

logger = logConfig(__name__)

def create_dirs():
    # Recreate tmpdir
    if os.path.isdir(cst.PATH_TMP_DIR):
        shutil.rmtree(cst.PATH_TMP_DIR)
    os.makedirs(cst.PATH_TMP_DIR)

def main():

    logger.info('Starting %s', cst.TOOL_NAME)

    # Parsing from cli
    args = parser.parse_from_command_line()

    # Init repo
    repo = Repository(args)

    # Handling cases
    cmd = args['command']
    if cmd == cst.PARSE_CMD_BUILD_PKG:
        logger.info('Resolving dependencies')
        packages_to_build = repo.resolve_build_dependencies(args['pkg_name'])

        # Prepare useful dirs
        create_dirs()
        repo.build_base(args['no_cache'])
        for pkg in packages_to_build:
            commit_mode = args['commit_all']
            tolerant = args['ignore_checksums']
            if pkg.get_package_name() == args['pkg_name'] and args['commit']:
                commit_mode = True
            repo.build_images(pkg, args['no_cache'], commit_mode, tolerant)
    else:
        logger.error("Unknown command '%s'. Stopping %s.", cmd, cst.TOOL_NAME)

    return 0

if __name__ == '__main__':
    sys.exit(main())
