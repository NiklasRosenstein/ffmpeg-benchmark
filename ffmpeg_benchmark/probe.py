import ffmpeg


def make_parser(subparsers):
    parser = subparsers.add_parser("probe", help="Get info about an input")

    parser.add_argument("--input", "-i")


def probe(input):
    probe = ffmpeg.probe(input)
    video_stream = next((
        stream for stream in probe['streams']
        if stream['codec_type'] == 'video'
    ), None)
    if video_stream is None:
        return {}
    return video_stream


def main(args):
    results = probe(
        input=args.input,
    )
    return results
