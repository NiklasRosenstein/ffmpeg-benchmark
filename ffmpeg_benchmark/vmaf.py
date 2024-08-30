import json
import time
import ffmpeg
import handystats
from ffmpeg_benchmark import probe

STATS_FILE = "vmaf.json"


def make_parser(subparsers):
    parser = subparsers.add_parser("vmaf", help="Evaluate quality with WMAF")

    parser.add_argument("--original-input", "-i")
    parser.add_argument("--new-input", "-I")
    parser.add_argument("--stats-file", default=STATS_FILE)


def vmaf(
    ori_input,
    new_input,
    stats_file=STATS_FILE,
):
    ori_stream = ffmpeg.input(ori_input)
    new_stream = ffmpeg.input(new_input)
    streams = (ori_stream, new_stream)

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

    t0 = time.time()
    stdout, stderr = output.run(
        capture_stdout=True,
        capture_stderr=True,
    )
    elapsed = time.time() - t0

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

    return {
        **results,
    }
