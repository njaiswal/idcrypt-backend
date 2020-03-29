import logging


def getLogger(name: str):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        '%(asctime)s,%(msecs)d %(levelname)-8s [%(name)s:%(funcName)s:%(lineno)d] %(message)s')
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.handlers = []  # === Make sure to add this line
    logger.addHandler(ch)
    logger.propagate = False  # === and this line so that duplicate log lines do not appear

    return logger
