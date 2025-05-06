import re
import time
import logging
import ffmpeg
import handystats
from ffmpeg_benchmark import probe

logger = logging.getLogger('ffmpeg_benchmark')
cmd_logger = logging.getLogger('ffmpeg_benchmark_cmd')

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
    ori_probe=None,
    new_probe=None,
):
    ori_stream = ffmpeg.input(ori_input)
    new_stream = ffmpeg.input(new_input)

    ori_probe = ori_probe or probe.probe(ori_input)
    new_probe = new_probe or probe.probe(new_input)

    ori_size = (ori_probe['streams'][0]['width'], ori_probe['streams'][0]['height'])
    new_size = (new_probe['streams'][0]['width'], new_probe['streams'][0]['height'])
    diff_size = ori_size != new_size

    if diff_size:
        ori_rescaled = ori_stream.filter(
            'scale',
            size=f"{ori_size[0]}x{ori_size[1]}",
            flags='bicubic',
        )
        new_rescaled = new_stream.filter(
            'scale',
            size=f"{ori_size[0]}x{ori_size[1]}",
            flags='bicubic',
        ).filter(
            'format',
            pix_fmts='yuv420p',
        ).filter(
            'fps',
            fps='30/1',
        )
        streams = (new_rescaled, ori_rescaled)
    else:
        streams = (new_stream, ori_stream)

    filter_graph = ffmpeg.filter(
        stream_spec=streams,
        filter_name='psnr',
        stats_file=stats_file
    )

    output_kwargs = {
        'format': 'null',
    }
    output = filter_graph.output('/dev/null', **output_kwargs)

    logger.info("Started PSNR %s<>%s", ori_input, new_input)
    cmd_logger.debug(output)
    t0 = time.time()
    try:
        stdout, stderr = output.run(
            capture_stdout=True,
            capture_stderr=True,
        )
        elapsed = time.time() - t0
    except ffmpeg._run.Error as err:
        logger.error(err.stderr.decode())
        raise

    psnr_data = []
    with open(stats_file) as fd:
        psnr_data = [
            dict(RE_PSNR.findall(line))
            for line in fd.readlines()
        ]
    psnr_stats = {}
    for key in psnr_data[0].keys():
        data = [float(d[key]) for d in psnr_data if d[key] != 'inf']
        psnr_stats.update(handystats.full_stats(
            data=data,
            prefix=f"{key}_",
        ))

    return {
        'elapsed': elapsed,
        'stdout': stdout,
        'stderr': stderr,
        **psnr_stats
    }


def main(args):
    results = psnr(
        ori_input=args.original_input,
        new_input=args.new_input,
        stats_file=args.stats_file,
    )
    return results
