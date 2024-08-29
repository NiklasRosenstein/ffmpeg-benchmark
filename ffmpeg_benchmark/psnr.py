import re
import time
import ffmpeg
from ffmpeg_benchmark import utils

RE_PSNR = re.compile(r'([^:]+):([a-z_0-9\.]+)')
STATS_FILE = "psnr_logfile.txt"


def make_parser(subparsers):
    parser = subparsers.add_parser("psnr", help="Evaluate quality with PSNR")

    parser.add_argument("--original-input", "-i")
    parser.add_argument("--new-input", "-I")
    parser.add_argument("--stats-file", default=STATS_FILE)


def psnr(
    ori_input,
    new_input,
    stats_file=STATS_FILE,
):
    # ffmpeg -i /tmp/foo.mp4 -i assets/BigBuckBunny_320x180.mp4  -lavfi psnr=stats_file=psnr_logfile.txt -f null -
    ori_stream = ffmpeg.input(ori_input)
    new_stream = ffmpeg.input(new_input)
    streams = (ori_stream, new_stream)

    filter_graph = ffmpeg.filter(
        stream_spec=streams,
        filter_name='psnr',
        stats_file=stats_file
    )

    output_kwargs = {
        'format': 'null',
    }
    output = filter_graph.output('/dev/null', **output_kwargs)

    t0 = time.time()
    stdout, stderr = output.run(
        capture_stdout=True,
        capture_stderr=True,
    )
    elapsed = time.time() - t0

    psnr_data = []
    with open(stats_file) as fd:
        psnr_data = [
            dict(RE_PSNR.findall(line))
            for line in fd.readlines()
        ]
    psnr_stats = {}
    for key in psnr_data[0].keys():
        data = [float(d[key]) for d in psnr_data if d[key] != 'inf']
        psnr_stats.update(utils.full_stats(data, f"{key}_"))

    return {
        'elapsed': elapsed,
        'stdout': stdout,
        'stderr': stderr,
        **psnr_stats
    }


def main(args):
    results = psnr(
        input=args.input,
        output=args.output,
        output_video_codec=args.output_video_codec,
    )

    return {
        **results,
    }
