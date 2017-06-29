import argparse

import constants as cst

class ParserError(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return 'Parsing failed: ' + self.msg

def parse_from_command_line():
    parser = argparse.ArgumentParser(prog=cst.TOOL_NAME)
    subparsers = parser.add_subparsers(help='sub-command help', dest='command')

    parser_cmd1 = subparsers.add_parser(cst.PARSE_CMD_INIT_WORKDIR, help="prepare working directory")
    parser_cmd2 = subparsers.add_parser(cst.PARSE_CMD_DOWNLOAD_REPO, help=cst.PARSE_CMD_DOWNLOAD_REPO+" help")
    parser_cmd3 = subparsers.add_parser(cst.PARSE_CMD_BUILD_PKG, help=cst.PARSE_CMD_BUILD_PKG+" help")
    parser_cmd4 = subparsers.add_parser(cst.PARSE_CMD_DOWNLOAD_PKG, help=cst.PARSE_CMD_DOWNLOAD_PKG+" help")

    parser_cmd3.add_argument(
        'pkg_name',
        help='name of the package to build')
    parser_cmd4.add_argument(
        'pkg_name',
        help='name of the package to build')
    parser_cmd3.add_argument(
        '--no-cache',
        dest='no_cache',
        action='store_true',
        default=False,
        required=False,
        help='do not use Docker cache to build')
    parser_cmd3.add_argument(
        '--nb-cores',
        dest='nb_cores',
        default=1,
        required=False,
        help='number of available cores to build packages')
    args = parser.parse_args()
    return vars(args)
