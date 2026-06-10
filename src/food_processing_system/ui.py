"""Terminal UI helpers.

The web-app niceties requested for this project — a modern look, clear visual
hierarchy, loading states, empty states and error states — are delivered here in
their command-line form: ANSI colours, framed banners, a lightweight spinner and
consistent status messages. Colours auto-disable when output is not a TTY or when
``NO_COLOR`` is set, so piping and CI logs stay clean.
"""

from __future__ import annotations

import itertools
import sys
import threading
import time
from collections.abc import Iterable, Iterator, Sequence
from contextlib import contextmanager

# Project branding, surfaced in the CLI footer.
PROJECT_NAME = "Food Processing System"
CONTACT_EMAIL = "aashish@marketdoctorsonline.com"
LINKS = {
    "LinkedIn": "https://in.linkedin.com/in/aashana1012",
    "GitHub": "https://github.com/aashishbharti04",
    "YouTube": "https://www.youtube.com/@CodeWithAsur",
    "Instagram": "https://www.instagram.com/asurwave1012",
}


class _Palette:
    """ANSI escape codes, blanked out when colours are disabled."""

    reset: str
    bold: str
    dim: str
    red: str
    green: str
    yellow: str
    blue: str
    magenta: str
    cyan: str

    def __init__(self, enabled: bool) -> None:
        codes = {
            "reset": "\033[0m",
            "bold": "\033[1m",
            "dim": "\033[2m",
            "red": "\033[31m",
            "green": "\033[32m",
            "yellow": "\033[33m",
            "blue": "\033[34m",
            "magenta": "\033[35m",
            "cyan": "\033[36m",
        }
        for name, code in codes.items():
            setattr(self, name, code if enabled else "")


class _Glyphs:
    """Symbol set, with an ASCII fallback for legacy encodings."""

    def __init__(self, unicode: bool) -> None:
        if unicode:
            (
                self.ok,
                self.err,
                self.warn,
                self.dot,
                self.arrow,
                self.tl,
                self.tr,
                self.bl,
                self.br,
                self.h,
                self.v,
                self.fade,
            ) = "✔✘⚠•▸╔╗╚╝═║┄"
        else:
            (
                self.ok,
                self.err,
                self.warn,
                self.dot,
                self.arrow,
                self.tl,
                self.tr,
                self.bl,
                self.br,
                self.h,
                self.v,
                self.fade,
            ) = ("[OK]", "[X]", "[!]", "*", ">", "+", "+", "+", "+", "=", "|", "-")


def _supports_unicode(stream) -> bool:
    """Return whether the stream's encoding can render our box/symbol glyphs."""
    encoding = getattr(stream, "encoding", None) or ""
    try:
        "✔═║┄▸".encode(encoding)
        return True
    except (UnicodeEncodeError, LookupError):
        return False


class Console:
    """A small console abstraction for consistent, themed output."""

    WIDTH = 60

    def __init__(self, use_colors: bool = True, stream=sys.stdout) -> None:
        # Prefer UTF-8 so the themed glyphs render on Windows consoles too.
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
        except (AttributeError, ValueError):  # pragma: no cover - stream specific
            pass
        self._stream = stream
        enabled = use_colors and stream.isatty()
        self.c = _Palette(enabled)
        self._color_enabled = enabled
        self.g = _Glyphs(_supports_unicode(stream))

    # -- Primitives ------------------------------------------------------ #

    def print(self, text: str = "") -> None:
        """Print a line of text, never crashing on an un-encodable character."""
        try:
            print(text, file=self._stream)
        except UnicodeEncodeError:  # pragma: no cover - legacy console fallback
            encoding = getattr(self._stream, "encoding", "ascii") or "ascii"
            print(text.encode(encoding, "replace").decode(encoding), file=self._stream)

    def banner(self, title: str, subtitle: str = "") -> None:
        """Print a framed title banner."""
        c, g = self.c, self.g
        line = g.h * self.WIDTH
        self.print(f"{c.cyan}{c.bold}{g.tl}{line}{g.tr}{c.reset}")
        self.print(f"{c.cyan}{c.bold}{g.v}{title.center(self.WIDTH)}{g.v}{c.reset}")
        if subtitle:
            self.print(
                f"{c.cyan}{g.v}{c.dim}{subtitle.center(self.WIDTH)}{c.reset}"
                f"{c.cyan}{g.v}{c.reset}"
            )
        self.print(f"{c.cyan}{c.bold}{g.bl}{line}{g.br}{c.reset}")

    def heading(self, text: str) -> None:
        """Print a section heading."""
        self.print(f"\n{self.c.bold}{self.c.blue}{self.g.arrow} {text}{self.c.reset}")

    # -- Status states --------------------------------------------------- #

    def success(self, text: str) -> None:
        self.print(f"{self.c.green}{self.g.ok} {text}{self.c.reset}")

    def error(self, text: str) -> None:
        """Render an error state."""
        self.print(f"{self.c.red}{self.g.err} {text}{self.c.reset}")

    def warning(self, text: str) -> None:
        self.print(f"{self.c.yellow}{self.g.warn} {text}{self.c.reset}")

    def info(self, text: str) -> None:
        self.print(f"{self.c.dim}{self.g.dot} {text}{self.c.reset}")

    def empty_state(self, text: str) -> None:
        """Render an empty state (the CLI analogue of an empty-list placeholder)."""
        f = self.g.fade * 3
        self.print(f"\n{self.c.dim}{f} {text} {f}{self.c.reset}\n")

    # -- Tables ---------------------------------------------------------- #

    def table(self, headers: Sequence[str], rows: Iterable[Sequence[object]]) -> None:
        """Render a simple aligned table."""
        str_rows = [[str(cell) for cell in row] for row in rows]
        widths = [len(h) for h in headers]
        for row in str_rows:
            for i, cell in enumerate(row):
                widths[i] = max(widths[i], len(cell))

        sep = f" {self.g.v} "
        cross = self.g.h + ("+" if self.g.h == "=" else "┼") + self.g.h

        def fmt(cells: Sequence[str]) -> str:
            return sep.join(cell.ljust(widths[i]) for i, cell in enumerate(cells))

        c = self.c
        self.print(f"{c.bold}{fmt(headers)}{c.reset}")
        self.print(c.dim + cross.join(self.g.h * w for w in widths) + c.reset)
        for row in str_rows:
            self.print(fmt(row))

    # -- Loading state --------------------------------------------------- #

    @contextmanager
    def spinner(self, message: str) -> Iterator[None]:
        """Show a loading spinner while a block of work runs."""
        if not self._color_enabled:
            self.info(message)
            yield
            return
        stop = threading.Event()
        frames = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏" if self.g.ok == "✔" else "|/-\\"

        def spin() -> None:
            for frame in itertools.cycle(frames):
                if stop.is_set():
                    break
                self._stream.write(f"\r{self.c.cyan}{frame}{self.c.reset} {message}")
                self._stream.flush()
                time.sleep(0.08)
            self._stream.write("\r" + " " * (len(message) + 4) + "\r")
            self._stream.flush()

        worker = threading.Thread(target=spin, daemon=True)
        worker.start()
        try:
            yield
        finally:
            stop.set()
            worker.join()

    # -- Footer ---------------------------------------------------------- #

    def footer(self) -> None:
        """Print the professional footer with contact and social links."""
        c = self.c
        self.print(f"\n{c.cyan}{self.g.h * (self.WIDTH + 2)}{c.reset}")
        self.print(f"{c.bold}{PROJECT_NAME}{c.reset}")
        self.print(f"{c.dim}Contact:{c.reset} {CONTACT_EMAIL}")
        for label, url in LINKS.items():
            self.print(f"{c.dim}{label}:{c.reset} {url}")
        self.print(f"{c.dim}© {PROJECT_NAME}. All rights reserved.{c.reset}")
        self.print(
            f"{c.dim}Open source - free for educational, learning and "
            f"community use.{c.reset}"
        )
        self.print(f"{c.cyan}{self.g.h * (self.WIDTH + 2)}{c.reset}")
