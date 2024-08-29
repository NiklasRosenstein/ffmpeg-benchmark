FROM linuxserver/ffmpeg

COPY . /ffmpeg-benchmark

RUN mkdir /assets

RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-venv git

RUN python3 -m venv /venv
RUN /venv/bin/pip install ffmpeg-python --no-cache-dir
RUN /venv/bin/pip install -e /ffmpeg-benchmark --no-cache-dir

RUN rm -rf \
    /var/lib/apt/lists/* \
    /var/tmp/* 

VOLUME /assets
VOLUME /ffmpeg-benchmark

CMD ["/bin/bash"]

ENTRYPOINT ["/bin/bash"]
