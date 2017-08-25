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

import argparse


from .constants import TOOL_NAME
from .constants import PARSE_CMD_BUILD_PKG


class ParserError(Exception):
    def __init__(self, msg):
        Exception.__init__(self)
        self.msg = msg
    def __str__(self):
        return 'Parsing failed: ' + self.msg

def parse_from_command_line():
    parser = argparse.ArgumentParser(prog=TOOL_NAME)
    subparsers = parser.add_subparsers(help='sub-command help', dest='command')

    parser_cmd1 = subparsers.add_parser(PARSE_CMD_BUILD_PKG, help=PARSE_CMD_BUILD_PKG+" help")

    parser_cmd1.add_argument(
        'pkg_name',
        help='name of the package to build')
    parser_cmd1.add_argument(
        '--ignore-checksums',
        dest='ignore_checksums',
        action='store_true',
        default=False,
        required=False,
        help='ignore checksums during build process')
    parser_cmd1.add_argument(
        '--no-cache',
        dest='no_cache',
        action='store_true',
        default=False,
        required=False,
        help='do not use Docker cache to build')
    parser_cmd1.add_argument(
        '--commit',
        dest='commit',
        action='store_true',
        default=False,
        required=False,
        help='commit checksums to contents file')
    parser_cmd1.add_argument(
        '--commit-all',
        dest='commit_all',
        action='store_true',
        default=False,
        required=False,
        help='commit checksums to contents file for package and its dependencies')
    parser_cmd1.add_argument(
        '--nb-cores',
        dest='nb_cores',
        default=1,
        required=False,
        help='number of available cores to build packages')
    args = parser.parse_args()
    return vars(args)
