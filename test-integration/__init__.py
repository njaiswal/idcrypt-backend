import logging

logger = logging.getLogger('root')
formatter = logging.Formatter('%(asctime)s,%(msecs)d %(levelname)-8s [%(name)s:%(lineno)d] %(message)s')
ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.setLevel(logging.DEBUG)
