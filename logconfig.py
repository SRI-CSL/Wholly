"""
  Logging configuration.
"""
import logging
import os
import sys


import constants as cst

_validLogLevels = ['ERROR', 'WARNING', 'INFO', 'DEBUG']

def logConfig(name):

    destination = os.getenv(cst.LOG_FILE)

    if destination:
        logging.basicConfig(filename=destination, level=logging.WARNING, format='%(levelname)s:%(message)s')
    else:
        logging.basicConfig(level=logging.WARNING, format='%(levelname)s:%(message)s')

    retval = logging.getLogger(name)

    # ignore old setting
    level = os.getenv(cst.LOG_LEVEL)

    if level:
        level = level.upper()
        if not level in _validLogLevels:
            logging.error('"%s" is not a valid value for %s. Valid values are %s', level, cst.LOG_LEVEL, _validLogLevels)
            sys.exit(1)
        else:
            retval.setLevel(getattr(logging, level))

    # Adjust the format if debugging
    if retval.getEffectiveLevel() == logging.DEBUG:
        formatter = logging.Formatter('%(levelname)s::%(module)s.%(funcName)s() at %(filename)s:%(lineno)d \n\t%(message)s')
        for h in logging.getLogger().handlers:
            h.setFormatter(formatter)

    return retval
