import time
import platform
import logging
import ffmpeg
from ffmpeg_benchmark import psnr

try:
    from probes import ProbeManager
    has_probes = True
except ImportError:
    has_probes = False

logger = logging.getLogger('ffmpeg_benchmark')


def make_parser(subparsers):
    parser = subparsers.add_parser("transcode", help="Evaluate transcoding performance")

    parser.add_argument("--input", "-i")
    parser.add_argument("--input-format", "-if", required=False)
    parser.add_argument("--input-video-codec", '-ic:v', required=False)
    parser.add_argument("--input-audio-codec", '-ic:a', required=False)

    parser.add_argument("-pre", help="Preset name")

    parser.add_argument("--output", "-o")
    parser.add_argument('--output-scale', required=False)
    parser.add_argument('--output-format', "-f", required=False)
    parser.add_argument('--output-video-bitrate', '-ob:v', required=False)
    parser.add_argument("--output-video-codec", '-oc:v', required=False)
    parser.add_argument("--output-audio-codec", '-oc:a', required=False)

    parser.add_argument("--enable-psnr", action="store_true")
    parser.add_argument("--psnr-stats-file", default=psnr.STATS_FILE)
    parser.add_argument("--enable-vmaf", action="store_true")
    parser.add_argument("--vmaf-stats-file", default="vmaf_logfile.txt")

    parser.add_argument(
        '--disable-monitoring', action="store_false", dest="monitoring_enabled",
    )
    parser.add_argument(
        '--monitoring-interval', type=int, default=5,
    )
    parser.add_argument(
        '--monitoring-probers', action='append'
    )
    parser.add_argument(
        '--monitoring-output', default="/dev/stderr"
    )


def transcode(
    input,
    output,
    output_video_codec=None,

    monitoring_enabled=False,
    monitoring_interval=False,
    monitoring_output=False,
    monitoring_probers=None,
):

    if not has_probes and monitoring_enabled:
        logger.warning("Monitoring is enabled without probes, please install it")
        monitoring_enabled = False
    if monitoring_enabled:
        if not monitoring_probers:
            monitoring_probers = [
                'probes.probers.system.CpuProber',
                'probes.probers.system.MemoryProber',
            ]
            sys_plat = platform.system()
            if sys_plat == 'Darwin':
                monitoring_probers += ['probes.probers.macos.MacosProber']
        probe_manager = ProbeManager(
            interval=monitoring_interval,
            probers=monitoring_probers,
        )
        probe_manager.start()

    input_kwargs = {}
    stream = ffmpeg.input(input, **input_kwargs)

    output_kwargs = {
    }
    if output_video_codec:
        output_kwargs['c:v'] = output_video_codec
    output = stream.output(output, **output_kwargs)

    t0 = time.time()
    stdout, stderr = output.run(
        capture_stdout=True,
        capture_stderr=True,
        overwrite_output=True,
    )
    elapsed = time.time() - t0

    if monitoring_enabled:
        probe_manager.stop()

    results = {
        'elapsed': elapsed,
        'stdout': stdout,
        'stderr': stderr,
    }

    return results


def parse_output(stdout, stderr):
    results = {}
    return results


def main(args):
    results = transcode(
        input=args.input,

        output=args.output,
        output_video_codec=args.output_video_codec,

        monitoring_enabled=args.monitoring_enabled,
        monitoring_interval=args.monitoring_interval,
        monitoring_output=args.monitoring_output,
        monitoring_probers=args.monitoring_probers,
    )

    results.update(parse_output(
        results.pop('stdout'),
        results.pop('stderr'),
    ))

    if args.enable_psnr:
        psnr_results = psnr.psnr(
            ori_input=args.input,
            new_input=args.output,
            stats_file=args.psnr_stats_file,
        )
        skipped = ('stdout', 'stderr')
        for key in psnr_results:
            if key in skipped:
                continue
            result_key = key.strip()
            if 'psnr' not in key:
                result_key = f"psnr_{result_key}"
            results[result_key] = psnr_results[key]

    return {
        **results,
    }
