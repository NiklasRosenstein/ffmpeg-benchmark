import re

RE_VERSION = re.compile(r'\d+\.\d+\.\d+')


def parse_version(line):
    search = RE_VERSION.search(line)
    if search:
        return search.group()
