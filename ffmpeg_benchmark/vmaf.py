# WIP
import time
import ffmpeg
from ffmpeg_benchmark import utils
from ffmpeg_benchmark import probe

STATS_FILE = "vmaf_logfile.txt"


def make_parser(subparsers):
    parser = subparsers.add_parser("wmaf", help="Evaluate quality with WMAF")

    parser.add_argument("--original-input", "-i")
    parser.add_argument("--new-input", "-I")
    parser.add_argument("--stats-file", default=STATS_FILE)


def vmaf(
    ori_input,
    new_input,
    stats_file=STATS_FILE,
):
    # ffmpeg -i videoToCompare.mp4 -i originalVideo.mp4 -lavfi libvmaf="model_path=vmaf_v0.6.1.pkl":log_path=vmaf_logfile.txt -f null -
    # ffmpeg -i /tmp/foo.mp4 -i assets/BigBuckBunny_320x180.mp4  -lavfi vmaf=stats_file=vmaf_logfile.txt -f null -
    ori_probe = probe.probe(ori_input)
    new_probe = probe.probe(new_input)
    import ipdb; ipdb.set_trace()

    ori_stream = ffmpeg.input(ori_input)
    new_stream = ffmpeg.input(new_input)
    streams = (ori_stream, new_stream)

    filter_graph = ffmpeg.filter(
        stream_spec=streams,
        filter_name='libvmaf',
    )

    output_kwargs = {
        'format': 'null',
    }
    output = filter_graph.output('/dev/null', **output_kwargs)

    t0 = time.time()
    stdout, stderr = output.run(
    )
    elapsed = time.time() - t0

    vmaf_data = []
    with open(stats_file) as fd:
        vmaf_data = [
            dict(RE_PSNR.findall(line))
            for line in fd.readlines()
        ]
    vmaf_stats = {}
    for key in vmaf_data[0].keys():
        data = [float(d[key]) for d in vmaf_data if d[key] != 'inf']
        vmaf_stats.update(utils.full_stats(data, f"{key}_"))

    return {
        'elapsed': elapsed,
        'stdout': stdout,
        'stderr': stderr,
        **vmaf_stats
    }


def main(args):
    return {}
