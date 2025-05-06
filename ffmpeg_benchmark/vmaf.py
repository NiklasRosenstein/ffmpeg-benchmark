import logging
import json
import time
import ffmpeg
import handystats
from ffmpeg_benchmark import probe

logger = logging.getLogger('ffmpeg_benchmark')
cmd_logger = logging.getLogger('ffmpeg_benchmark_cmd')

STATS_FILE = "vmaf.json"


def make_parser(subparsers):
    parser = subparsers.add_parser("vmaf", help="Evaluate quality with WMAF")

    parser.add_argument("--original-input", "-i", required=True)
    parser.add_argument("--new-input", "-I", required=True)
    parser.add_argument("--stats-file", default=STATS_FILE)


def vmaf(
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
        )
        streams = (new_rescaled, ori_rescaled)
    else:
        streams = (new_stream, new_stream)

    filter_graph = ffmpeg.filter(
        stream_spec=streams,
        filter_name='libvmaf',
        log_fmt='json',
        log_path=stats_file,
    )

    output_kwargs = {
        'format': 'null',
    }
    output = filter_graph.output('/dev/null', **output_kwargs)

    logger.info("Started VMAF %s<>%s", ori_input, new_input)
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

    with open(stats_file) as fd:
        raw_results = json.load(fd)

    vmaf_stats = {
        'version': raw_results['version'],
        'num_frames': len(raw_results['frames']),
        'fps': raw_results['fps'],
    }
    frames_stats = raw_results['frames']
    for key in frames_stats[0]['metrics'].keys():
        data = [float(d['metrics'][key]) for d in frames_stats]
        vmaf_stats.update(handystats.full_stats(
            data,
            prefix=f"{key}_",
        ))

    return {
        'elapsed': elapsed,
        'stdout': stdout,
        'stderr': stderr,
        **vmaf_stats
    }


def main(args):
    results = vmaf(
        ori_input=args.original_input,
        new_input=args.new_input,
        stats_file=args.stats_file,
    )
    return results
