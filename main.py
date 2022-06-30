import logging

from httpx import main
from utils import util_logger

util_logger.set_logger_config("super-converter")
logger = logging.getLogger("super-converter")


def test():
    logger.info('===== test info =====')
    logger.error('===== test error =====')


if __name__ == '__main__':
    test()
