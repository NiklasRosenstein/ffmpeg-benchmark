# ffmpeg-benchmark

ffmpeg-benchmark is a handy tool to measure ffmpeg performance with different samples, configuration and hardware.
It's goal is to measure raw performance in terms of latency and FPS, as well as to assess quality with [VMAF] and [PSNR].

[VMAF]: https://wiki.x266.mov/docs/metrics/VMAF
[PSNR]: https://wiki.x266.mov/docs/metrics/PSNR

__Table of Contents__

<!-- toc -->
  * [Quickstart](#quickstart)
    * [Docker](#docker)
    * [Uv](#uv)
    * [Fetch input video from URL](#fetch-input-video-from-url)
  * [Usage](#usage)
* [Contribute](#contribute)
<!-- end toc -->

## Quickstart

[Uv]: https://docs.astral.sh/uv/
[linuxserver/ffmpeg]: https://docs.linuxserver.io/images/docker-ffmpeg/
[Big Buck Bunny]: https://peach.blender.org/download/

The easiest way to use ffmpeg-benchmark is to run it via Docker. Alternatively, you can run it directly using [Uv], but you need to have ffmpeg installed on your system. You'll also need a sample video file to test with. A good starting point is [Big Buck Bunny].

```console
$ wget https://download.blender.org/demo/movies/BBB/bbb_sunflower_2160p_60fps_normal.mp4.zip
$ unzip bbb_sunflower_2160p_60fps_normal.mp4.zip
$ du -h bbb_sunflower_2160p_60fps_normal.mp4
643M    bbb_sunflower_2160p_60fps_normal.mp4
```

### Docker

```console
$ docker run --pull always --rm -it -v $PWD:/assets \
  ghcr.io/niklasrosenstein/ffmpeg-benchmark:main -v 2 transcode \
  -i /assets/bbb_sunflower_2160p_60fps_normal.mp4
```

To test with hardware acceleration, check out the [linuxserver/ffmpeg] Docker image documentation for how to configure the `docker run` command. The `ffmpeg-benchmark transcode` command supports the `--hwaccel` option that will be passed to `ffmpeg`.

### Uv

```console
$ uvx git+https://github.com/niklasrosenstein/ffmpeg-benchmark -v 2 \
  transcode -i bbb_sunflower_2160p_60fps_normal.mp4
```

### Fetch input video from URL

The `ffmpeg-benchmark transcode` command supports fetching the input from a URL. The file _may_ be a ZIP file with a single video file inside.

```console
$ docker run --pull always --rm -it -v $PWD:/assets \
  ghcr.io/niklasrosenstein/ffmpeg-benchmark:main -v 2 transcode \
  -i https://download.blender.org/demo/movies/BBB/bbb_sunflower_2160p_60fps_normal.mp4.zip
```

## Usage

<!-- runcmd code: COLUMNS=100 uv run ffmpeg-benchmark --help -->
```
usage: ffmpeg-benchmark [-h] [-v VERBOSITY] [-q] {probe,transcode,psnr,vmaf} ...

positional arguments:
  {probe,transcode,psnr,vmaf}
    probe               Get info about an input
    transcode           Evaluate transcoding performance
    psnr                Evaluate quality with PSNR
    vmaf                Evaluate quality with WMAF

options:
  -h, --help            show this help message and exit
  -v, --verbosity VERBOSITY
                        0: Muted, 1: Info, 2: Verbose, 3: Full verbose 4: ffmpeg verbose
  -q, --quiet           Completly disable any output
```
<!-- end runcmd -->


# Contribute

This project is created with ❤️ for free by [Cloud Mercato] under BSD License. Feel free to contribute by submitting a pull request or an issue.

[Cloud Mercato]: https://www.cloud-mercato.com/
