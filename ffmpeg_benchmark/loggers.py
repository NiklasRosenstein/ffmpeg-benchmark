import logging
from ffmpeg._run import get_args


class FfmpegCmdFormatter(logging.Formatter):
    default_fmt = '[%(asctime)s %(pathname)s:%(lineno)d]: %(message)s'

    def __init__(self, fmt=None, *args, **kwargs):
        if fmt is None:
            fmt = self.default_fmt
        super().__init__(fmt=fmt, *args, **kwargs)

    def format(self, record):
        if not isinstance(record.msg, str):
            cmd_args = ['ffmpeg'] + get_args(record.msg)
            record.msg = ' '.join(cmd_args)
        return super().format(record)


debug_formatter = logging.Formatter('[%(asctime)s %(pathname)s:%(lineno)d %(levelname)s]: %(message)s')

logger = logging.getLogger("ffmpeg_benchmark")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

cmd_formatter = FfmpegCmdFormatter()
cmd_logger = logging.getLogger("ffmpeg_benchmark_cmd")
cmd_handler = logging.StreamHandler()
cmd_handler.setLevel(logging.DEBUG)
cmd_handler.setFormatter(cmd_formatter)
cmd_logger.addHandler(cmd_handler)


def set_logger(verbosity):
    verbosity = verbosity
    logger_level = max((10, 40-(10+verbosity*10)))
    logger.setLevel(logger_level)
    if verbosity == 3:
        handler.setFormatter(debug_formatter)

    cmd_logger_level = max((10, 50-(10+verbosity*10)))
    cmd_logger.setLevel(cmd_logger_level)

    return logger
