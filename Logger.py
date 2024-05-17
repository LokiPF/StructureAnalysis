import logging
import logging.config
import yaml


class Logger:
    def __init__(self, module: str = 'root'):
        with open('logging.ini', 'r') as f:
            config = yaml.safe_load(f.read())
            logging.config.dictConfig(config)
            self.logger = logging.getLogger(module)
