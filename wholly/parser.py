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
