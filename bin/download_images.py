#!/usr/bin/env python3

import os
import re
import sys
from pathlib import Path
from typing import Optional

import requests
from ruamel.yaml import YAML

yaml = YAML()


class Downloader:
    def __init__(self):
        self.changes = False

    def reformat_to_dict(self, data: dict) -> dict:
        for k, v in data.items():
            if v is None:
                continue

            # convert bare string values to dict
            elif isinstance(v, str) and v.startswith("https://"):
                print("Converting to dict", k)
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
        print("Downloading", path_parts)

        for k, v in data.items():
            if v is None:
                continue

            if isinstance(v, dict):
                if 'error' in v:
                    print("WARNING: Skipping due to previous error:", k)
                    continue

                if 'img' in v:
                    file = download_image(
                        parts=path_parts,
                        label=k,
                        url=v['img'],
                        slug=v.get('slug'),
                    )
                    if file:
                        if v.get('path') != file:
                            v['path'] = file
                            self.changes = True
                    else:
                        v['error'] = True
                        self.changes = True

                else:
                    # recurse
                    self.download_all_images(
                        data=v, path_parts=path_parts + [k]
                    )

            else:
                raise ValueError(f"Unexpected type at {k!r} -- {v!r}")


def read_and_download(yaml_file: str):
    print("Reading", yaml_file)
    data = yaml.load(open(yaml_file))

    dl = Downloader()
    try:
        # dl.reformat_to_dict(data=data)
        dl.download_all_images(data=data, path_parts=['img'])
    except KeyboardInterrupt:
        pass

    # write data back
    if dl.changes:
        print("Writing changes back to file")
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
        print("Image already downloaded:", filepath)
        return str(filepath)
    else:
        print("Downloading image for", filepath)

    print("GET", url)
    try:
        resp = requests.get(url, timeout=2)
    except requests.exceptions.ReadTimeout as err:
        print(f"WARNING: received {err!r} while loading {url!r}")
        return None

    if resp.status_code != 200:
        print(f"WARNING: received HTTP {resp.status_code} from {url!r}")
        return None

    open(filepath, 'wb').write(resp.content)

    return str(filepath)


if __name__ == "__main__":
    yaml_file = sys.argv[1]
    read_and_download(yaml_file)
