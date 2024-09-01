# https://ffmpeg.org/ffmpeg.html
# https://python-ffmpeg.readthedocs.io/en/stable/
# https://download.blender.org/peach/bigbuckbunny_movies/
import argparse

from ffmpeg_benchmark import probe
from ffmpeg_benchmark import transcode
from ffmpeg_benchmark import psnr
from ffmpeg_benchmark import vmaf
from ffmpeg_benchmark import __version__
from ffmpeg_benchmark.loggers import set_logger

ACTIONS = {
    'probe': probe.main,
    'transcode': transcode.main,
    'psnr': psnr.main,
    'vmaf': vmaf.main,
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbosity", type=int, default=0, help="0: Muted, 1: Info, 2: Verbose, 3: Full verbose 4: ffmpeg verbose")
    parser.add_argument(
        '-q', '--quiet',
        action="store_true",
        help="Completly disable any output",
    )

    subparsers = parser.add_subparsers(dest="action")
    probe.make_parser(subparsers)
    transcode.make_parser(subparsers)
    psnr.make_parser(subparsers)
    vmaf.make_parser(subparsers)

    args = parser.parse_args()

    set_logger(0 if args.quiet else args.verbosity)

    action = ACTIONS[args.action]

    print(f"version: {__version__}")
    result = action(args)
    for key, value in result.items():
        print(f"{key}: {value}")


if __name__ == '__main__':
    main()
