import re
import time
import platform
import logging
import ffmpeg
from ffmpeg_benchmark import probe
from ffmpeg_benchmark import psnr
from ffmpeg_benchmark import vmaf

try:
    from probes import ProbeManager
    has_probes = True
except ImportError:
    has_probes = False

logger = logging.getLogger('ffmpeg_benchmark')

RE_BENCH = re.compile(r'([^=]+)=([0-9\.]+)[^ ]* *')

# Scale presets
# uhd2160
# uhd4320
# 4k
# hd1080
# hd720
# hd480
# vga
# svga
# xfix
# xsrv

def make_parser(subparsers):
    parser = subparsers.add_parser("transcode", help="Evaluate transcoding performance")

    parser.add_argument("--input", "-i")
    parser.add_argument("--input-format", "-if", required=False)
    parser.add_argument("--input-video-codec", '-ic:v', required=False)
    parser.add_argument("--input-audio-codec", '-ic:a', required=False)

    parser.add_argument("-pre", help="Preset name")

    parser.add_argument("--output", "-o", default="/dev/null")
    parser.add_argument('--output-format', "-f", required=False)
    parser.add_argument('--output-scale', required=False)
    parser.add_argument('--output-video-bitrate', '-ob:v', required=False)
    parser.add_argument("--output-video-codec", '-oc:v', required=False)
    parser.add_argument("--output-audio-codec", '-oc:a', required=False)
    parser.add_argument("--output-disable-audio", action="store_true")

    parser.add_argument("--enable-psnr", action="store_true")
    parser.add_argument("--psnr-stats-file", default=psnr.STATS_FILE)
    parser.add_argument("--enable-vmaf", action="store_true")
    parser.add_argument("--vmaf-stats-file", default=vmaf.STATS_FILE)

    parser.add_argument("--hwaccel", default="none")

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


class Transcoder:
    def __init__(
        self,
        input,

        output,
        output_format=None,
        output_scale=None,
        output_video_codec=None,
        output_disable_audio=None,

        hwaccel='none',
    ):
        self.input = input

        self.output = output
        self.output_format = output_format
        self.output_scale = output_scale
        self.output_video_codec = output_video_codec
        self.output_disable_audio = output_disable_audio

        self.hwaccel = hwaccel

    @property
    def input_probe(self):
        if not hasattr(self, '_input_probe'):
            self._input_probe = probe.probe(self.input)
        return self._input_probe

    @property
    def input_probe_data(self):
        if not hasattr(self, '_input_probe_data'):
            self._input_probe_data = {
                f"input_{key}": value
                for key, value in probe.extract_data(self.input_probe).items()
            }
        return self._input_probe_data

    @property
    def output_probe(self):
        if self.output == '/dev/null':
            return {}
        if not hasattr(self, '_output_probe'):
            self._output_probe = probe.probe(self.output)
        return self._output_probe

    @property
    def output_probe_data(self):
        if self.output == '/dev/null':
            return {}
        if not hasattr(self, '_output_probe_data'):
            self._output_probe_data = {
                f"output_{key}": value
                for key, value in probe.extract_data(self.output_probe).items()
            }
        return self._output_probe_data

    def run(self):
        input_kwargs = {
            'hwaccel': self.hwaccel,
        }
        logger.debug('Input kwargs: %s', input_kwargs)
        stream = ffmpeg.input(self.input, **input_kwargs)

        if self.output_scale:
            stream = stream.filter(
                'scale', size=self.output_scale,
            )

        output_kwargs = {
            'benchmark': None,
        }
        if self.output_video_codec:
            output_kwargs['c:v'] = self.output_video_codec
        if self.output == '/dev/null':
            output_kwargs['format'] = self.output_format or 'null'
        if self.output_disable_audio:
            output_kwargs['an'] = None

        logger.debug('Output kwargs: "%s", %s', self.output, output_kwargs)
        output_stream = stream.output(self.output, **output_kwargs)

        t0 = time.time()
        try:
            stdout, stderr = output_stream.run(
                capture_stdout=True,
                capture_stderr=True,
                overwrite_output=True,
            )
            elapsed = time.time() - t0
        except ffmpeg._run.Error as err:
            logger.error(err.stderr.decode())
            raise

        results = {
            'elapsed': elapsed,
            'stdout': stdout,
            'stderr': stderr,
            **self.input_probe_data,
            **self.output_probe_data,
            'output_format': self.output_format,
            'output_scale': self.output_scale,
            'output_video_codec': self.output_video_codec,

            'fps': self.input_probe_data['input_video_nb_frames'] / elapsed,
        }

        return results


def transcode(**kwargs):
    transcoder = Transcoder(**kwargs)
    results = transcoder.run()
    return results


def parse_output(stdout, stderr):
    results = {}
    stderr = stderr.decode()
    for line in stderr.splitlines():
        if line.startswith('bench:'):
            results.update(RE_BENCH.findall(line.split(': ')[1]))
    stdout = stdout.decode()
    for line in stdout.splitlines():
        pass
    return results


def main(args):
    monitoring_enabled = args.monitoring_enabled
    if not has_probes and monitoring_enabled:
        logger.warning("Monitoring is enabled without probes, please install it")
        monitoring_enabled = False
    if monitoring_enabled:
        monitoring_probers = args.monitoring_probers
        if not monitoring_probers:
            monitoring_probers = [
                'probes.probers.system.CpuProber',
                'probes.probers.system.MemoryProber',
            ]
            sys_plat = platform.system()
            if sys_plat == 'Darwin':
                monitoring_probers += ['probes.probers.macos.MacosProber']
        probe_manager = ProbeManager(
            interval=args.monitoring_interval,
            probers=monitoring_probers,
        )
        probe_manager.start()

    results = transcode(
        input=args.input,

        output=args.output,
        output_format=args.output_format,
        output_scale=args.output_scale,
        output_video_codec=args.output_video_codec,
    )

    if monitoring_enabled:
        probe_manager.stop()

    results.update(parse_output(
        results.pop('stdout'),
        results.pop('stderr'),
    ))

    if args.enable_psnr and args.output == '/dev/null':
        logger.warning("PSNR cannot used with a stream to %s", args.output)
    elif args.enable_psnr:
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

    if args.enable_vmaf and args.output == '/dev/null':
        logger.warning("VMAF cannot used with a stream to %s", args.output)
    elif args.enable_vmaf:
        vmaf_results = vmaf.vmaf(
            ori_input=args.input,
            new_input=args.output,
            stats_file=args.vmaf_stats_file,
        )
        skipped = ('stdout', 'stderr')
        for key in vmaf_results:
            if key in skipped:
                continue
            result_key = key.strip()
            if 'vmaf' not in key:
                result_key = f"vmaf_{result_key}"
            results[result_key] = vmaf_results[key]

    return {
        **results,
    }
