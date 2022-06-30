import os


class Conf(object):

    @classmethod
    def get_log_path(cls):
        _log_path = '/sanford/logs/super-converter'
        if not os.path.exists(_log_path):
            _log_path = 'D:\\CodePy\\super-converter\\logs'
        return _log_path
