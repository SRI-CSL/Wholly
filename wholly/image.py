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

import sys
import os
import subprocess
import shutil
import json


from .constants import TOOL_NAME
from .constants import PATH_TMP_DIR

from .logconfig import logConfig

logger = logConfig(__name__)

def get_base_image_name():
    return TOOL_NAME+'-base-image'

def get_package_image_name(pkg_name, subpackage=None):
    img_name = TOOL_NAME+'-'+pkg_name
    if subpackage:
        img_name = img_name+'-'+subpackage
    return img_name

# Build Docker image according to the Dockerfile put into the given working directory
def build_docker_image(img_name, working_dir, no_cache, df_filename, b_move_dockerfile):
    no_cache_arg = ''
    if no_cache:
        no_cache_arg = '--no-cache'
    build_cmd = 'docker build -t ' + img_name + ' . -f ' + df_filename + ' ' + no_cache_arg
    logPath = os.path.abspath(os.path.join(PATH_TMP_DIR, 'dockerbuild-'+img_name+'.log'))
    logFile = open(logPath, 'w')
    logFile.write('\n*** INFO ***\n')
    logFile.write('Build command: ' + build_cmd)
    ret = subprocess.call(
        build_cmd,
        shell=True,
        stdout=logFile,
        stderr=logFile,
        cwd=working_dir)
    # Move Dockerfile to tmp for debugging purposes
    if b_move_dockerfile:
        src_df_path = os.path.join(working_dir, df_filename)
        dest_df_filename = 'Dockerfile-'+img_name
        dest_df_path = os.path.join(PATH_TMP_DIR, dest_df_filename)
        shutil.move(src_df_path, dest_df_path)
    logFile.flush()
    logFile.close()
    if ret != 0:
        logger.error('Building package %s failed. Stopping.', img_name)
        logger.error('See %s for more details.', logPath)
        sys.exit(1)

def get_subpkg_hash(img_name):
    req_cmd = 'docker inspect --format=\'{{json .RootFS.Layers}}\' ' + img_name
    try:
        ret = subprocess.check_output(
            req_cmd,
            shell=True)
        ret = json.loads(ret)
        return str(ret[0])
    except subprocess.CalledProcessError:
        return 'No image found locally'
