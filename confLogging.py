import logging

def configLog(logger):
    """Initial configuration logs."""
    logger.setLevel(logging.DEBUG)
    fmt = logging.Formatter('''%(asctime)s - %(name)s -
                            [%(levelname)s] - %(message)s''')
    err_stream = logging.StreamHandler()
    err_stream.setLevel(logging.ERROR)
    err_stream.setFormatter(fmt)
    logger.addHandler(err_stream)
    gen_stream = logging.FileHandler('manageVM.log')
    gen_stream.setLevel(logging.INFO)
    gen_stream.setFormatter(fmt)
    logger.addHandler(gen_stream)
    return logger
