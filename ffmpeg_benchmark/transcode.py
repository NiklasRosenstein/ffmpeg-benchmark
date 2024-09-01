import re
import time
import platform
import logging
from concurrent.futures import ThreadPoolExecutor

import ffmpeg
import handystats

from ffmpeg_benchmark import probe
from ffmpeg_benchmark import psnr
from ffmpeg_benchmark import vmaf
from ffmpeg_benchmark import utils

try:
    from probes import ProbeManager
    has_probes = True
except ImportError:
    has_probes = False

logger = logging.getLogger('ffmpeg_benchmark')
cmd_logger = logging.getLogger('ffmpeg_benchmark_cmd')

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
PRESETS = (
    'ultrafast',
    'superfast',
    'veryfast',
    'faster',
    'fast',
    'medium',
    'slow',
    'slower',
    'veryslow',
)
TUNES = (
    'film',
    'animation',
    'grain',
)


def make_parser(subparsers):
    parser = subparsers.add_parser("transcode", help="Evaluate transcoding performance")

    parser.add_argument("--processes", "-p", type=int, default=1, help="Number of simulataneous ffmpeg process.")
    parser.add_argument("--filter-threads", type=int, help="Number of threads are used to process a filter pipeline.")

    parser.add_argument("--input", "-i")
    parser.add_argument("--input-format", "-if", required=False)
    parser.add_argument("--input-video-codec", '-ic:v', required=False)
    parser.add_argument("--input-audio-codec", '-ic:a', required=False)
    parser.add_argument("--input-disable-audio", action='store_true')
    parser.add_argument("--input-thread-queue-size", type=int, required=False, help="Max number of queued packets when reading from the file or device")

    parser.add_argument("--preset", help="Preset name", required=False, choices=PRESETS)
    parser.add_argument("--crf", type=int, required=False, help="From 0 (loseless), max depends of codec")
    parser.add_argument("--tune", required=False, choices=TUNES)

    parser.add_argument("--output", "-o", default="/dev/null")
    parser.add_argument('--output-format', "-f", required=False)
    parser.add_argument('--output-scale', required=False)
    parser.add_argument('--output-video-bitrate', '-ob:v', required=False)
    parser.add_argument("--output-video-codec", '-oc:v', required=False)
    # parser.add_argument("--output-audio-codec", '-oc:a', required=False)
    parser.add_argument("--output-disable-audio", action="store_true")
    parser.add_argument("--output-thread-queue-size", type=int, required=False, help="Max number of packets that may be queued to each muxing thread.")

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

        processes=1,
        filter_threads=None,

        input_disable_audio=False,
        input_thread_queue_size=None,

        preset=None,
        crf=None,
        tune=None,

        output=None,
        output_format=None,
        output_scale=None,
        output_video_codec=None,
        output_disable_audio=None,
        output_thread_queue_size=None,

        hwaccel='none',

        verbosity=1,
    ):
        self.processes = processes
        self.filter_threads = filter_threads

        self.input = input
        self.input_disable_audio = input_disable_audio
        self.input_thread_queue_size = input_thread_queue_size

        self.preset = preset
        self.crf = crf
        self.tune = tune

        self.output = output
        self.output_format = output_format
        self.output_scale = output_scale
        self.output_video_codec = output_video_codec
        self.output_disable_audio = output_disable_audio
        self.output_thread_queue_size = output_thread_queue_size

        self.hwaccel = hwaccel

        self.verbosity = verbosity

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

    def parse_output(self, stdout, stderr):
        results = {}
        stderr = stderr.decode()

        lines = stderr.splitlines()
        version = utils.parse_version(lines[0])
        if version:
            results['ffmpeg_version'] = version
        for line in lines[1:]:
            if line.startswith('bench:'):
                results.update(RE_BENCH.findall(line.split(': ')[1]))
        stdout = stdout.decode()
        for line in stdout.splitlines():
            pass
        return results

    def run(self):
        # Make input
        input_kwargs = {
            'hwaccel': self.hwaccel,
        }
        if self.input_disable_audio:
            input_kwargs['an'] = None
        if self.filter_threads is not None:
            input_kwargs['filter_threads'] = self.filter_threads
        if self.input_thread_queue_size is not None:
            input_kwargs['thread_queue_size'] = self.input_thread_queue_size
        logger.debug('Input kwargs: %s', input_kwargs)
        stream = ffmpeg.input(self.input, **input_kwargs)
        # Apply filter
        if self.output_scale:
            stream = stream.filter(
                'scale', size=self.output_scale,
            )
        # Make output
        output_kwargs = {
            'benchmark': None,
        }
        if self.preset:
            output_kwargs['preset'] = self.preset
        if self.crf is not None:
            output_kwargs['crf'] = self.crf
        if self.tune:
            output_kwargs['tune'] = self.tune
        if self.output_video_codec:
            output_kwargs['c:v'] = self.output_video_codec
        if self.output == '/dev/null':
            output_kwargs['format'] = self.output_format or 'null'
        if self.output_disable_audio:
            output_kwargs['an'] = None
        if self.output_thread_queue_size is not None:
            output_kwargs['thread_queue_size'] = self.output_thread_queue_size

        logger.debug('Output kwargs: "%s", %s', self.output, output_kwargs)
        output_stream = stream.output(self.output, **output_kwargs)
        # Run transcoding
        def _run(i):
            logger.info("Started stream #%s", i)
            cmd_logger.debug(output_stream)
            t0 = time.time()
            try:
                stdout, stderr = output_stream.run(
                    capture_stdout=True,
                    capture_stderr=True,
                    overwrite_output=True,
                )
                elapsed = time.time() - t0
            except ffmpeg._run.Error as err:
                logger.info("stderr: %s", err.stderr.decode())
                return {
                    'ok': False,
                    'stdout': err.stdout,
                    'stderr': err.stderr,
                    **self.parse_output(err.stdout, err.stderr),
                }
            if self.verbosity >= 4:
                logger.debug("stdout: %s", stdout.decode())
                logger.debug("stderr: %s", stderr.decode())
            return {
                'ok': True,
                'elapsed': elapsed,
                'stdout': stdout,
                'stderr': stderr,
                **self.parse_output(stdout, stderr),
            }

        futures = []
        with ThreadPoolExecutor(max_workers=self.processes) as executor:
            for i in range(self.processes):
                futures.append(executor.submit(_run, i))
        results = [f.result() for f in futures]
        # Compute values
        ffmpeg_version = results[0]['ffmpeg_version']

        elapseds = [r['elapsed'] for r in results if r['ok']]
        in_nb_frames = self.input_probe_data['input_video_nb_frames']
        fpss = [(in_nb_frames/e) for e in elapseds]
        errors = [r for r in results if not r['ok']]
        error_count = len(errors)

        results = {
            'ffmpeg_version': ffmpeg_version,
            'processes': self.processes,
            'filter_threads': self.filter_threads,

            'preset': self.preset,
            'crf': self.crf,
            'tune': self.tune,

            'input': self.input,
            **self.input_probe_data,
            'input_disable_audio': self.input_disable_audio,
            'input_thread_queue_size': self.input_thread_queue_size,

            'output': self.output,
            **self.output_probe_data,
            'output_format': self.output_format,
            'output_scale': self.output_scale,
            'output_video_codec': self.output_video_codec,
            'output_disable_audio': self.output_disable_audio,
            'output_thread_queue_size': self.output_thread_queue_size,

            'error_count': error_count,
            'elapseds': elapseds,
            'fpss': fpss,
            **handystats.full_stats(elapseds, prefix='elapsed_'),
            **handystats.full_stats(fpss, prefix='fps_'),
        }

        return results


def transcode(**kwargs):
    transcoder = Transcoder(**kwargs)
    results = transcoder.run()
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
        logger.info("Started monitoring")
        logger.debug("Monitoring prober: %s", monitoring_probers)

    results = transcode(
        hwaccel=args.hwaccel,
        processes=args.processes,
        filter_threads=args.filter_threads,

        input=args.input,
        input_disable_audio=args.input_disable_audio,
        input_thread_queue_size=args.input_thread_queue_size,

        preset=args.preset,
        crf=args.crf,
        tune=args.tune,

        output=args.output,
        output_format=args.output_format,
        output_scale=args.output_scale,
        output_video_codec=args.output_video_codec,
        output_disable_audio=args.output_disable_audio,
        output_thread_queue_size=args.output_thread_queue_size,

        verbosity=args.verbosity,
    )

    if monitoring_enabled:
        probe_manager.stop()
        logger.info("Stopped monitoring")
        probe_data = probe_manager.get_results()

        cpu_percents = [v['cpu_percent'] for v in probe_data['cpu'].values()]
        results.update(handystats.full_stats(cpu_percents, prefix='cpu_percent_'))

        mem_percents = [v['virtual_memory']['percent'] for v in probe_data['memory'].values()]
        results.update(handystats.full_stats(mem_percents, prefix='mem_percent_'))

        if 'nvidia' in probe_data:
            power_usages = [v['power_usage'] for v in probe_data['nvidia'].values()]
            results.update(handystats.full_stats(power_usages, prefix='nvidia_power_usage'))

            temps = [v['temperature'] for v in probe_data['nvidia'].values()]
            results.update(handystats.full_stats(temps, prefix='nvidia_temperature'))

    if args.processes == results['error_count']:
        logger.error('All operations failed (%s)', args.processes)
        return results

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

    return results
