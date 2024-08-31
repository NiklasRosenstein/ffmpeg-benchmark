import ffmpeg


def make_parser(subparsers):
    parser = subparsers.add_parser("probe", help="Get info about an input")

    parser.add_argument("--input", "-i")


def probe(input):
    probe = ffmpeg.probe(input)
    return probe


def extract_data(probe):
    fmt = probe['format']
    data = {
        'bit_rate': int(fmt['bit_rate']),
        'duration': float(fmt['duration']),
        'format_name': fmt['format_name'],
        'nb_programs': fmt['nb_programs'],
        'nb_streams': fmt['nb_streams'],
        'probe_score': fmt['probe_score'],
        'size': int(fmt['size']),
    }

    video = next((
        stream for stream in probe['streams']
        if stream['codec_type'] == 'video'
    ), None)
    if video is not None:
        data.update({
            'video_bit_rate': video['bit_rate'],
            'video_codec_name': video['codec_name'],
            'video_height': video['height'],
            'video_width': video['width'],
            'video_pix_fmt': video['pix_fmt'],
            'video_nb_frames': int(video['nb_frames']),
        })

    audio = next((
        stream for stream in probe['streams']
        if stream['codec_type'] == 'audio'
    ), None)
    if audio is not None:
        data.update({
            'audio_bit_rate': audio['bit_rate'],
            'audio_codec_name': audio['codec_name'],
            'audio_nb_frames': int(audio['nb_frames']),
            'audio_sample_rate': int(audio['sample_rate']),
        })
    return data


def main(args):
    results = probe(
        input=args.input,
    )
    return results
