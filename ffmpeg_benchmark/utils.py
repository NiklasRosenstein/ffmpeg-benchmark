from .loggers import logger
from contextlib import ExitStack
from pathlib import Path
from shutil import copyfileobj
from zipfile import ZipFile
import re
import requests

RE_VERSION = re.compile(r'\d+\.\d+\.\d+')


def parse_version(line):
    search = RE_VERSION.search(line)
    if search:
        return search.group()


def download_video_file(url, filename):
    """
    Download a video file from a given URL and save it to a specified filename.
    """

    filename = Path(filename)
    response = requests.get(url, stream=True)

    with ExitStack() as on_exit:

        # Write the response to a temporary file first so we can unpack it later if it is a zip file,
        # otherwise we simply rename it.
        tmpfile = filename.with_name(filename.name + ".tmp")
        on_exit.callback(lambda: Path(tmpfile).unlink(missing_ok=True))
        with tmpfile.open("wb") as fp:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    fp.write(chunk)

        is_zip = url.endswith(".zip") or response.headers.get('Content-Type') == 'application/zip'
        if is_zip:
            zip_fp = on_exit.enter_context(ZipFile(tmpfile, 'r'))
            if len(members := zip_fp.namelist()) != 1:
                raise ValueError("ZIP file must contain exactly one file. Got: " + str(members))

            with filename.open("wb") as dst, zip_fp.open(members[0], 'r') as src:
                logger.info("Extracting %s to %s", members[0], filename)
                copyfileobj(src, dst)

        else:
            tmpfile.rename(filename)

    return filename
