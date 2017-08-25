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
