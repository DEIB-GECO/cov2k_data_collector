from loguru import logger
import warnings
import sys


logger.remove()  # removes default logger to stderr with level DEBUG
# on console print from level INFO on
logger.add(sink=sys.stderr,
           level='TRACE',
           format=#"<green>{time:YYYY-MM-DD HH:mm:ss Z}</green> | "
                  "<level>{level: <8}</level> | "
                  "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
           colorize=True,
           backtrace=True,
           diagnose=True,
           enqueue=True)

# redirect warnings
def customwarn(message, category, filename, lineno, file=None, line=None):
    logger.warning(warnings.formatwarning(message, category, filename, lineno))

warnings.showwarning = customwarn
