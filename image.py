import sys
import os
import subprocess
import shutil
import logging

import constants as cst

def get_base_image_name():
    return cst.TOOL_NAME+'-base-image'

def get_package_image_name(pkg_name, subpackage=None):
    img_name = cst.TOOL_NAME+'-'+pkg_name
    if subpackage:
        img_name = img_name+'-'+subpackage
    return img_name

# Build Docker image according to the Dockerfile put into the given working directory
def build_docker_image(img_name, working_dir, no_cache, df_filename, b_move_dockerfile):
    no_cache_arg = ''
    if no_cache:
        no_cache_arg = '--no-cache'
    build_cmd = 'docker build -t ' + img_name + ' . -f ' + df_filename + ' ' + no_cache_arg
    logFile = open(os.path.join(cst.PATH_TMP_DIR, 'dockerbuild-'+img_name+'.log'), 'w')
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
        dest_df_path = os.path.join(cst.PATH_TMP_DIR, dest_df_filename)
        shutil.move(src_df_path, dest_df_path)
    logFile.flush()
    logFile.close()
    if not ret == 0:
        logging.error('Building package ' + img_name + ' failed. Stopping.')
        sys.exit(1)
