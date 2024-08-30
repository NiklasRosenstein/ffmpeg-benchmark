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


def extract_data(probe):
    return {
        'bit_rate': int(probe['bit_rate']),
        # 'bits_per_raw_sample': int(probe['bits_per_raw_sample']),
        'codec_name': probe['codec_name'],
        'duration': float(probe['duration']),
        'height': probe['height'],
        'width': probe['width'],
        'nb_frames': int(probe['nb_frames']),
        'pix_fmt': probe['pix_fmt'],
        # 'field_order': probe['field_order'],
    }


def main(args):
    results = probe(
        input=args.input,
    )
    return results
