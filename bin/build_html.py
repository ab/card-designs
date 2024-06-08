#!/usr/bin/env python3

import logging
import sys
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader
from ruamel.yaml import YAML

yaml = YAML()


REPO_ROOT = Path(__file__).parent.parent


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


class PageGenerator:
    def __init__(self, yaml_path: Path, template_dir: Path, web_dir: Path):
        self.yaml_path = yaml_path
        logger.debug("Loading %s", yaml_path)
        self.data = yaml.load(open(yaml_path))
        self.template_dir = template_dir
        self.web_dir = web_dir

        self.jinja_env = Environment(
            loader=FileSystemLoader(template_dir), keep_trailing_newline=True
        )

    def _is_leaf(self, d: dict) -> bool:
        return 'img' in d or 'path' in d

    def build(self) -> None:
        logger.debug("PageGenerator.build()")

        header = self.render_template("index.header.html", data={})
        footer = self.render_template("index.footer.html", data={})

        body = self.build_body(data=self.data, level=1)

        index_outfile = self.web_dir.joinpath("index.html")
        logger.info("Writing to %s", index_outfile)
        with open(index_outfile, "w") as f:
            f.write(header + body + footer)

        logger.info("Done!")

    def render_template(self, basename: str, data: dict) -> str:
        tmpl = self.jinja_env.get_template(basename)
        return tmpl.render(**data)

    def build_body(self, data: dict, level: int) -> str:
        h_tag = f"h{level:d}"
        out = ""
        for k, v in data.items():
            if v is None:
                continue

            indent = "  " * (level + 1)

            if self._is_leaf(v):
                card_html = self.render_template(
                    "card.html", {"label": k, "card": v}
                )
                out += indent + "  " + card_html.replace(
                    "\n", "\n" + indent + "  "
                ).rstrip() + "\n"
            else:
                logger.debug("Section: %s %r", "#" * level, k)
                out += indent + f"<div class='section level{level:d}'>\n"
                out += indent + f"  <{h_tag}>{k}</{h_tag}>\n"
                out += indent + "  <ul>\n"
                # recurse
                out += self.build_body(data=v, level=level + 1)

                out += indent + "  </ul>\n"
                out += indent + "</div>\n"

        return out

    def list_templates(self) -> list[Path]:
        templates = list(self.template_dir.glob("*.html"))
        if not templates:
            raise Exception(f"Found no *.html files in {template_dir!r}")
        return templates


if __name__ == "__main__":
    if len(sys.argv) > 1:
        sys.stderr.write("usage: build_html.py\n")
        sys.exit(1)

    yaml_file = REPO_ROOT.joinpath("cards.yaml")
    template_dir = REPO_ROOT.joinpath("templates")
    web_dir = REPO_ROOT.joinpath("web")

    pg = PageGenerator(
        yaml_path=yaml_file, template_dir=template_dir, web_dir=web_dir
    )
    pg.build()
