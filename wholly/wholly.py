#!/usr/bin/env python
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
from __future__ import absolute_import

import sys
import os
import shutil

from .constants import PATH_TMP_DIR
from .constants import TOOL_NAME
from .constants import PARSE_CMD_BUILD_PKG

from .repository import Repository
from .parser import parse_from_command_line
from .logconfig import logConfig

logger = logConfig(__name__)

def create_dirs():
    # Recreate tmpdir
    if os.path.isdir(PATH_TMP_DIR):
        shutil.rmtree(PATH_TMP_DIR)
    os.makedirs(PATH_TMP_DIR)

def main():

    logger.info('Starting %s', TOOL_NAME)

    # Parsing from cli
    args = parse_from_command_line()

    # Init repo
    repo = Repository(args)

    # Handling cases
    cmd = args['command']
    if cmd == PARSE_CMD_BUILD_PKG:
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
        logger.error("Unknown command '%s'. Stopping %s.", cmd, TOOL_NAME)

    return 0

if __name__ == '__main__':
    sys.exit(main())
