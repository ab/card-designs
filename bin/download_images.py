#!/usr/bin/env python3

import logging
import os
import re
import sys
from contextlib import AbstractContextManager
from pathlib import Path
from typing import Optional

import requests
from ruamel.yaml import YAML

yaml = YAML()


SKIP_ERRORED = False


class chdir_ctx(AbstractContextManager):
    """
    Non thread-safe context manager to change the current working directory.

    Replace this with contextlib.chdir in Python 3.11+
    """

    def __init__(self, path):
        self.path = path
        self._old_cwd = []

    def __enter__(self):
        self._old_cwd.append(os.getcwd())
        os.chdir(self.path)

    def __exit__(self, *excinfo):
        os.chdir(self._old_cwd.pop())


class ColorFormatter(logging.Formatter):

    def __init__(self, fmt: Optional[str] = None):
        gray = "\x1b[90;1m"
        yellow = "\x1b[93;1m"
        red = "\x1b[91;1m"
        reset = "\x1b[0m"

        if not fmt:
            fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

        formats = {
            logging.DEBUG: gray + fmt + reset,
            logging.INFO: fmt,
            logging.WARNING: yellow + fmt + reset,
            logging.ERROR: red + fmt + reset,
            logging.CRITICAL: red + fmt + reset,
        }

        self._formatters = {
            k: logging.Formatter(formatstr) for k, formatstr in formats.items()
        }

        for f in self._formatters.values():
            f.default_msec_format = "%s.%03d"

    def format(self, record):
        formatter = self._formatters[record.levelno]
        return formatter.format(record)


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
handler.setFormatter(
    ColorFormatter(fmt="%(asctime)s [%(levelname)s] %(message)s")
)
logger.addHandler(handler)


class Downloader:
    def __init__(self):
        self.changes = False

    def reformat_to_dict(self, data: dict) -> dict:
        for k, v in data.items():
            if v is None:
                continue

            # convert bare string values to dict
            elif isinstance(v, str) and v.startswith("https://"):
                logger.info("Converting to dict: %r", k)
                data[k] = {
                    "img": v,
                }
                v = data[k]
                self.changes = True

            elif isinstance(v, dict):
                if 'img' in v:
                    # already an image dict
                    pass
                else:
                    # recurse
                    data[k] = self.reformat_to_dict(v)

            else:
                raise ValueError(f"Unexpected type {k!r}: {v!r}")

        return data

    def download_all_images(self, data: dict, path_parts: list[str]) -> None:
        """
        Recursively download all images from nested YAML data.

        Note: this may mutate values in data to add error and convert to dict
        format.
        """
        logger.info("Visiting: %r", path_parts)

        for k, v in data.items():
            if v is None:
                continue

            if isinstance(v, dict):
                if 'error' in v:
                    if SKIP_ERRORED:
                        logger.warning("Skipping due to previous error: %r", k)
                        continue

                if 'img' in v:
                    file = download_image(
                        parts=path_parts,
                        label=k,
                        url=v['img'],
                        slug=v.get('slug'),
                    )

                    if not file:
                        v['error'] = True
                        self.changes = True
                        continue

                    # update path as needed
                    if v.get('path') != file:
                        v['path'] = file
                        self.changes = True

                    # clear error as needed
                    if v.get('error'):
                        del v['error']

                else:
                    # recurse
                    self.download_all_images(
                        data=v, path_parts=path_parts + [k]
                    )

            else:
                raise ValueError(f"Unexpected type at {k!r} -- {v!r}")


def read_and_download(yaml_file: str, web_dir: str):
    logger.info("Reading %r", yaml_file)
    data = yaml.load(open(yaml_file))

    dl = Downloader()
    try:
        # dl.reformat_to_dict(data=data)
        with chdir_ctx(web_dir):
            dl.download_all_images(data=data, path_parts=['img'])
    except KeyboardInterrupt:
        pass

    # write data back
    if dl.changes:
        logger.warning("Writing changes back to file")
        yaml.dump(data, open(yaml_file, "w"))


def make_slug(label: str) -> str:
    return re.sub(r'[^a-zA-Z0-9\.()_+-]', '-', label)


def download_image(
    parts: list[str], label: str, url: str, slug: Optional[str] = None
) -> Optional[str]:

    if not slug:
        slug = make_slug(label)

    parent = Path(*parts)
    parent.mkdir(parents=True, exist_ok=True)

    ext = os.path.splitext(url)[1]

    filepath = parent.joinpath(slug + ext)

    if filepath.is_file() and filepath.stat().st_size > 0:
        logger.debug("Image already downloaded: %r", filepath)
        return str(filepath)
    else:
        logger.info("Downloading image for %r", filepath)

    logger.info("GET %s", url)
    try:
        resp = requests.get(url, timeout=5)
    except requests.exceptions.ReadTimeout as err:
        logger.warning("received %r while loading %r", err, url)
        return None

    if resp.status_code != 200:
        logger.warning("received HTTP %r from %r", resp.status_code, url)
        return None

    open(filepath, 'wb').write(resp.content)

    return str(filepath)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: download_images.py YAML_FILE WEB_DIR")
        print()
        print("for example: download_images.py cards.yaml web")
        sys.exit(1)
    yaml_file = sys.argv[1]
    web_dir = sys.argv[2]
    read_and_download(yaml_file, web_dir)
