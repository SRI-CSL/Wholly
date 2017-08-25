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

from .image import get_package_image_name
from .image import get_base_image_name

from .constants import PATH_RES_DIR
from .constants import PATH_TMP_CONTENTS_FILE
from .constants import RELEASE_DIRECTORY

from .logconfig import logConfig

logger = logConfig(__name__)



#from pykwalify.core import Core
#from pykwalify.errors import PyKwalifyException

class Package(object):
    def __init__(self, package_name, recipe_file_contents, contents_file_contents, args):
        # TODO: Validate package yaml file against schema
        #try:
        #    c = Core(source_data=yamlContents, schema_files=[os.path.join(os.getcwd(), 'tool/schemas/package.yaml')])
        #    logging.getLogger('pykwalify.core').setLevel(logging.CRITICAL)
        #    c.validate(raise_exception=True)
        #except PyKwalifyException as e:
        #    logging.error('For package ' + packageName + '-' + packageVersion + ' -> ' + e.msg)
        #    sys.exit(1)

        self.package_name = package_name
        self.args = args
        self.parse_recipe_file(yaml.load(recipe_file_contents))
        if contents_file_contents:
            self.subpackages_contents = yaml.load(contents_file_contents)
            for k in self.subpackages_contents:
                if isinstance(self.subpackages_contents[k], list):
                    self.subpackages_contents[k] = {
                        'files': self.subpackages_contents[k],
                        'checksum': 'none'
                    }
                else:
                    self.subpackages_contents[k]['checksum'] = self.subpackages_contents[k].pop('checksum', 'No checksum provided')
        else:
            self.subpackages_contents = {}
        self.dockerfile = None

    def parse_recipe_file(self, recipe_file_contents):
        self.variables = recipe_file_contents.pop('variables', {})
        self.source = recipe_file_contents.pop('source', None)
        self.resources = recipe_file_contents.pop('resources', None)
        self.prepare_commands = recipe_file_contents.pop('prepare', None)
        self.build_commands = recipe_file_contents.pop('build', None)
        self.dependencies = recipe_file_contents.pop('dependencies', {})
        self.revision = recipe_file_contents.pop('revision', None)

        self.release_date = recipe_file_contents.pop('release_date', None)
        if not self.release_date:
            logger.error('Package '+self.package_name+' does not provide release date. Stopping.')
            sys.exit(1)
        self.release_date = self.release_date.__format__('%Y%m%d%H%M')

        if self.variables:
            self.variables = {k: v for d in self.variables for k, v in d.items()}

        ## Add global variables to parsing
        self.variables['__RES_DIR__'] = '/build'
        self.variables['__INSTALL_DIR__'] = '/usr'
        self.variables['__SRC_DIR__'] = '/build/' + self.package_name
        self.variables['__NB_CORES__'] = self.args['nb_cores']

    def get_build_dependencies(self):
        return self.dependencies

    def write_df_line(self, strv):
        self.dockerfile.write(strv + '\n')

    def write_df_newline(self):
        self.write_df_line('')

    def write_df_multiline_args(self, prefix, args, separator=''):
        nargs = len(args)
        if nargs == 1:
            self.write_df_line(prefix + ' ' + args[0])
        else:
            for i in range(nargs):
                if i == 0:
                    self.write_df_line(prefix + ' ' + args[0] + ' ' + separator + ' \\')
                elif i == nargs - 1:
                    self.write_df_line('  ' + args[i])
                else:
                    self.write_df_line('  ' + args[i] + ' ' + separator + ' \\')

    def write_df_comment(self, strv):
        self.write_df_line('# ' + strv)

    def write_df_base_part(self, img_name, stage_name=None):
        df_line = 'FROM ' + img_name
        if stage_name:
            df_line = df_line + ' as ' + stage_name
        self.write_df_line(df_line)
        self.write_df_newline()

    def write_df_deps_base_part(self):
        if not self.dependencies:
            return
        for pkg_name in self.dependencies:
            for subpkg_name in self.dependencies[pkg_name]:
                img_name = get_package_image_name(pkg_name, subpkg_name)
                self.write_df_base_part(img_name, img_name+'-files')

    def write_df_bring_deps_files(self):
        if not self.dependencies:
            return
        self.write_df_comment('Bringing dependencies in')
        for pkg_name in self.dependencies:
            for subpkg_name in self.dependencies[pkg_name]:
                img_name = get_package_image_name(pkg_name, subpkg_name)
                stage_name = img_name+'-files'
                self.write_df_line('COPY --from='+stage_name+' / /')
        self.write_df_newline()

    def write_df_copy_res_part(self):
        if not self.resources:
            return
        self.write_df_comment('Copying resources')
        for res_name in self.resources:
            res_path = os.path.join(PATH_RES_DIR, res_name)
            self.write_df_line('COPY ' + res_path + ' /build')
        self.write_df_newline()

    def write_df_prep_part(self):
        if not self.prepare_commands:
            return
        self.write_df_comment('Preparing')
        self.write_df_line('WORKDIR /build')
        for prep_cmd in self.prepare_commands:
            prep_cmd = prep_cmd.format(**self.variables)
            self.write_df_line('RUN ' + prep_cmd)
        self.write_df_newline()

    def write_df_get_source_part(self):
        self.write_df_comment('Getting source')
        source_dir = self.get_package_name()
        self.write_df_line('WORKDIR /build')
        if 'git' in self.source:
            repo_src = self.source['git'].format(**self.variables)
            self.write_df_line('RUN git clone ' + repo_src + ' ' + source_dir)
        elif 'tar.gz' in self.source:
            tar_src = self.source['tar.gz'].format(**self.variables)
            self.write_df_line('RUN curl -L "' + tar_src + '" -o src.tar.gz')
            self.write_df_line('RUN mkdir ' + source_dir + ' && tar xf src.tar.gz -C ' + source_dir + ' --strip-components 1')
        elif 'tar.bz2' in self.source:
            tar_src = self.source['tar.bz2'].format(**self.variables)
            self.write_df_line('RUN curl -L "' + tar_src + '" -o src.tar.bz2')
            self.write_df_line('RUN mkdir ' + source_dir + ' && tar xf src.tar.bz2 -C ' + source_dir + ' --strip-components 1')
        elif 'tgz' in self.source:
            tar_src = self.source['tgz'].format(**self.variables)
            self.write_df_line('RUN curl -L "' + tar_src + '" -o src.tgz')
            self.write_df_line('RUN mkdir ' + source_dir + ' && tar xf src.tgz -C ' + source_dir + ' --strip-components 1')
        self.write_df_newline()

    def write_df_build_part(self):
        if not self.build_commands:
            return
        self.write_df_comment('Building')
        self.write_df_line('WORKDIR ' + os.path.join('/build', self.get_package_name()))
        for build_cmd in self.build_commands:
            build_cmd = build_cmd.format(**self.variables)
            self.write_df_line('RUN ' + build_cmd)
        self.write_df_newline()

    def write_df_copy(self, src_path, dest_path, build_stage):
        self.write_df_line('COPY --from='+build_stage+' '+src_path+' '+dest_path)

    def write_build_dockerfile(self, df_file):
        self.dockerfile = df_file
        self.write_df_deps_base_part()
        self.write_df_base_part(get_base_image_name())
        self.write_df_bring_deps_files()
        self.write_df_copy_res_part()
        self.write_df_prep_part()
        self.write_df_get_source_part()
        self.write_df_build_part()
        self.dockerfile.flush()
        self.dockerfile.close()

    def write_subpackage_dockerfile(self, df_file, contents_list, subpkg_name):
        build_files_stage_name = 'build'
        self.dockerfile = df_file

        # Packaging files
        self.write_df_base_part(get_package_image_name(self.package_name), build_files_stage_name)
        self.write_df_line('COPY '+PATH_TMP_CONTENTS_FILE+' '+PATH_TMP_CONTENTS_FILE)
        self.write_df_line('RUN mkdir -p '+RELEASE_DIRECTORY)
        if contents_list:
            if subpkg_name == 'bin':
                # Try to strip binaries automatically
                self.write_df_line('RUN while read p; do strip "$p" || true; done < '+PATH_TMP_CONTENTS_FILE)
            self.write_df_line('RUN while read p; do cp --parents -r "$p" '+RELEASE_DIRECTORY+'; done < '+PATH_TMP_CONTENTS_FILE)
            self.write_df_line('RUN find '+RELEASE_DIRECTORY+' -exec touch -h -t '+self.release_date+r' {} \;')
        self.write_df_line('RUN rm '+PATH_TMP_CONTENTS_FILE)

        # Releasing
        self.write_df_base_part('scratch')
        self.write_df_line('COPY --from='+build_files_stage_name+' '+RELEASE_DIRECTORY+' /')
        self.dockerfile.flush()
        self.dockerfile.close()

    def get_package_name(self):
        return self.package_name

    def get_subpackages_contents(self):
        return self.subpackages_contents
