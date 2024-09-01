ffmpeg-benchmark
~~~~~~~~~~~~~~~~

ffmpeg-benchmark is a handy tool to measure ffmpeg performance with different samples, configuration and hardware.


The goal is currently:

  - Measure raw performance: latency and FPS
  - Assess quality with VMAF and PSNR

.. contents:: Table of Contents
   :depth: 3
   :local:

Get started
===========

Install
-------

Simple as::

   pip install https://github.com/cloudmercato/ffmpeg-benchmark/archive/refs/heads/main.zip

For monitoring you may install `Probes`_::

  pip install https://github.com/cloudmercato/Probes/archive/refs/heads/main.zip


Usage
-----

::

  # ffmpeg-benchmark --help
  usage: ffmpeg-benchmark [-h] [--verbosity VERBOSITY] [-q] {probe,transcode,psnr,vmaf} ...
  
  positional arguments:
    {probe,transcode,psnr,vmaf}
      probe               Get info about an input
      transcode           Evaluate transcoding performance
      psnr                Evaluate quality with PSNR
      vmaf                Evaluate quality with WMAF
  
  options:
    -h, --help            show this help message and exit
    --verbosity VERBOSITY
                          0: Muted, 1: Info, 2: Debug, 3: More, 4: ffmpeg verbose
    -q, --quiet           Completly disable any output

Docker usage
------------

We made a Dockerfile from `linuxserver/ffmpeg:latest`_ to facilitate the deployment with a fully compiled version of ffmpeg.

Here's a basic usage::

  # docker build -t ffmpeg-benchmark .
  # docker run -it -rm -v /ffmpeg-assets/:/assets ffmpeg-benchmark

The volume ``/assets`` is use for enabling persistence of input/output files.

Contribute
==========

This project is created with ❤️ for free by `Cloud Mercato`_ under BSD License. Feel free to contribute by submitting a pull request or an issue.

.. _`Probes`: https://github.com/cloudmercato/Probes
.. _`linuxserver/ffmpeg:latest`: https://github.com/linuxserver/docker-ffmpeg
.. _`Cloud Mercato`: https://www.cloud-mercato.com/

