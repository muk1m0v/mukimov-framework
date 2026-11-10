"""Markdown → ANSI terminal renderer for ``mukimov``.

Public API::

    from mukimov.text import markdown

    markdown.print("# Hello")
    text = markdown.render("**Hello**")
    print(text)

* :func:`render` returns a ready-to-print ANSI string and prints nothing.
* :func:`print` renders and writes the result to the terminal.

Implementation notes:

* Markdown parsing is delegated to the small, stable ``markdown-it-py``
  dependency (``commonmark`` preset + ``table``/``strikethrough`` rules).
  This module only implements the ANSI renderer on top of the token
  stream — no hand-written Markdown parser, no giant regex soup.
* Pre-existing ANSI codes (e.g. from ``mukimov.color``) are preserved,
  not removed: leading/trailing color runs are set aside before parsing
  (so ``green("**Hi!**")`` parses exactly like plain ``**Hi!**``) and
  any inner codes are hidden behind punctuation-led placeholders that
  disturb CommonMark emphasis flanking as little as possible.
* Math/LaTeX syntax (``$...$`` / ``$$...$$``) is intentionally NOT
  interpreted in 0.1.6: unknown syntax passes through as plain text and
  never crashes the renderer. See :func:`_render_math_passthrough` as the
  future extension point.

.. note::
    This module defines a function named :func:`print`. Inside this
    module the builtin is accessed as ``builtins.print`` to avoid
    shadowing issues.
"""

from __future__ import annotations

import builtins
import re
import unicodedata

try:
    from markdown_it import MarkdownIt
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "mukimov.text.markdown requires the 'markdown-it-py' package. "
        "Run: python -m pip install --upgrade mukimov"
    ) from exc

try:
    from wcwidth import wcwidth as _wcwidth
except ImportError:  # fallback to unicodedata (stdlib) when wcwidth is missing
    _wcwidth = None  # type: ignore[assignment]

__all__ = ["render", "print"]

# ---------------------------------------------------------------------------
# ANSI styles
# ---------------------------------------------------------------------------

RESET = "\x1b[0m"
BOLD = "\x1b[1m"
ITALIC = "\x1b[3m"
UNDERLINE = "\x1b[4m"
STRIKE = "\x1b[9m"
DIM = "\x1b[2m"
GRAY = "\x1b[90m"
CYAN = "\x1b[96m"

CODE_STYLE = CYAN
LINK_STYLE = (UNDERLINE, CYAN)
HR_WIDTH = 40
BULLET = "\u2022"  # •

# ---------------------------------------------------------------------------
# Markdown parser (single shared instance; parsing is stateless per call).
# ---------------------------------------------------------------------------

_parser = MarkdownIt("commonmark").enable(["table", "strikethrough"])

# ---------------------------------------------------------------------------
# Pre-existing ANSI protection (mukimov.color compatibility)
# ---------------------------------------------------------------------------

_ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
_PH_A = "\ue000"
_PH_B = "\ue001"
# NOTE: the placeholder starts with a literal "." on purpose. A closer such
# as the second ``**`` in ``**Hi!**`` cannot close in front of a
# letter-like character (standard CommonMark flanking rules — even a plain
# ``X`` breaks it), but it can close in front of punctuation. The dot keeps
# emphasis parsing identical to the unprotected text in more cases; the
# whole placeholder (dot included) is removed again on restore.
_PH_RE = re.compile(r"\.\ue000(\d+)\ue001")


def _split_boundary_ansi(text: str) -> tuple[str, str, str]:
    """Split leading/trailing ANSI runs off *text*.

    ``green("**Success!**")`` is ``ANSI + "**Success!**" + ANSI``: parsing
    the core alone behaves exactly like parsing plain Markdown, so emphasis
    flanking can never be disturbed by the outer color codes.
    """
    leading = ""
    trailing = ""
    core = text
    head = re.match(r"(?:\x1b\[[0-9;?]*[A-Za-z])+", core)
    if head:
        leading = head.group(0)
        core = core[len(leading):]
    if core:
        tail = re.search(r"(?:\x1b\[[0-9;?]*[A-Za-z])+$", core)
        if tail:
            trailing = tail.group(0)
            core = core[: -len(trailing)]
    return leading, core, trailing


def _protect_ansi(text: str) -> tuple[str, list[str]]:
    """Replace remaining (inner) ANSI sequences with placeholders.

    Returns the protected text plus the list of original sequences so they
    can be restored after rendering. Placeholders use private-use code
    points that Markdown parsing leaves untouched as plain text.
    """
    saved: list[str] = []

    def _repl(match: re.Match[str]) -> str:
        saved.append(match.group(0))
        return f".{_PH_A}{len(saved) - 1}{_PH_B}"

    return _ANSI_RE.sub(_repl, text), saved


def _restore_ansi(text: str, saved: list[str]) -> str:
    """Restore ANSI sequences previously hidden by :func:`_protect_ansi`."""

    def _repl(match: re.Match[str]) -> str:
        idx = int(match.group(1))
        if 0 <= idx < len(saved):
            return saved[idx]
        return ""

    return _PH_RE.sub(_repl, text)


# ---------------------------------------------------------------------------
# Terminal display width (Unicode-aware, ANSI-agnostic)
# ---------------------------------------------------------------------------


def _char_width(char: str) -> int:
    """Display width of a single character in a terminal column."""
    if char in ("\n", "\r", "\t", "\x00"):
        return 0
    if unicodedata.combining(char):
        return 0
    if _wcwidth is not None:
        width = _wcwidth(char)
        return width if width > 0 else 0
    if unicodedata.category(char) in ("Mn", "Me", "Cf", "Cc"):
        return 0
    if unicodedata.east_asian_width(char) in ("W", "F"):
        return 2
    return 1


def _visible_width(text: str) -> int:
    """Visible terminal width: ANSI codes and placeholders count as 0."""
    clean = _ANSI_RE.sub("", text)
    clean = _PH_RE.sub("", clean)
    return sum(_char_width(ch) for ch in clean)


def _pad_cell(text: str, width: int, align: str) -> str:
    """Pad *text* (which may contain ANSI) to visible *width*."""
    extra = max(0, width - _visible_width(text))
    if align == "right":
        return " " * extra + text
    if align == "center":
        left = extra // 2
        right = extra - left
        return " " * left + text + " " * right
    return text + " " * extra


# ---------------------------------------------------------------------------
# Inline renderer (spans with correct style nesting / restore)
# ---------------------------------------------------------------------------


class _InlineRenderer:
    """Renders inline token children with an explicit style stack.

    Every opened frame is closed with RESET followed by re-emitting the
    still-active outer styles, so nested ``**bold *italic***`` restores
    bold after italic ends and no style ever leaks into later output.
    """

    def __init__(self) -> None:
        self._parts: list[str] = []
        self._stack: list[list[str]] = []
        self._links: list[tuple[str, int]] = []

    # -- style stack ------------------------------------------------------
    def open(self, *codes: str) -> None:
        frame = list(codes)
        self._stack.append(frame)
        for code in frame:
            self._parts.append(code)

    def close(self) -> None:
        if not self._stack:
            return
        self._stack.pop()
        self._parts.append(RESET)
        for frame in self._stack:
            for code in frame:
                self._parts.append(code)

    def text(self, value: str) -> None:
        self._parts.append(value)

    def value(self) -> str:
        while self._stack:
            self.close()
        return "".join(self._parts)

    # -- token feeding ----------------------------------------------------
    def feed(self, children: list) -> None:
        for tok in children or []:
            ttype = tok.type
            if ttype == "text":
                self.text(tok.content)
            elif ttype == "code_inline":
                self.open(CODE_STYLE)
                self.text(tok.content)
                self.close()
            elif ttype == "strong_open":
                self.open(BOLD)
            elif ttype == "strong_close":
                self.close()
            elif ttype == "em_open":
                self.open(ITALIC)
            elif ttype == "em_close":
                self.close()
            elif ttype in ("s_open", "strike_open"):
                self.open(STRIKE)
            elif ttype in ("s_close", "strike_close"):
                self.close()
            elif ttype == "link_open":
                href = ""
                try:
                    attrs = dict(tok.attrs or {})
                except (TypeError, ValueError):
                    attrs = {}
                href = str(attrs.get("href", "") or "")
                self._links.append((href, len(self._parts)))
                self.open(*LINK_STYLE)
            elif ttype == "link_close":
                self.close()  # closes the LINK_STYLE frame
                href, _mark = self._links.pop() if self._links else ("", 0)
                inner_text = _ANSI_RE.sub("", "".join(self._parts[_mark:]))
                inner_text = _PH_RE.sub("", inner_text)
                # Skip the suffix for autolinks like <https://...> where the
                # visible text already is the URL.
                if href and inner_text != href:
                    self.text(" ")
                    self.open(DIM)
                    self.text(f"({href})")
                    self.close()
            elif ttype == "image":
                try:
                    attrs = dict(tok.attrs or {})
                except (TypeError, ValueError):
                    attrs = {}
                src = str(attrs.get("src", "") or "")
                alt = ""
                if tok.children:
                    alt = "".join(
                        c.content for c in tok.children if hasattr(c, "content")
                    )
                self.text(alt)
                if src:
                    self.text(" ")
                    self.open(DIM)
                    self.text(f"({src})")
                    self.close()
            elif ttype in ("softbreak", "hardbreak"):
                self.text("\n")
            elif ttype == "html_inline":
                self.text(tok.content)
            else:
                # Unknown/forward-compatible inline token: render nested
                # children if any, otherwise keep raw content as plain text
                # (this also covers future math tokens — never crash).
                if getattr(tok, "children", None):
                    self.feed(tok.children)
                elif getattr(tok, "content", ""):
                    self.text(tok.content)


def _render_inline(children: list, outer: tuple[str, ...] = ()) -> str:
    renderer = _InlineRenderer()
    if outer:
        renderer.open(*outer)
    renderer.feed(children)
    return renderer.value()


# ---------------------------------------------------------------------------
# Block renderer
# ---------------------------------------------------------------------------


def _parse_align(attrs) -> str:
    try:
        style = dict(attrs or {}).get("style", "")
    except (TypeError, ValueError):
        return "left"
    style = str(style)
    if "text-align:right" in style:
        return "right"
    if "text-align:center" in style:
        return "center"
    return "left"


def _render_math_passthrough(text: str) -> str:
    """Future LaTeX extension point (planned, NOT implemented in 0.1.6).

    Currently returns the text unchanged so ``$E = mc^2$`` and ``$$...$$``
    blocks pass through as plain text without breaking the renderer.
    """
    return text


class _BlockRenderer:
    def render_blocks(self, tokens: list) -> list[str]:
        """Render top-level (or nested) block tokens into terminal lines."""
        lines: list[str] = []
        i = 0
        n = len(tokens)
        while i < n:
            tok = tokens[i]
            ttype = tok.type
            if ttype == "paragraph_open":
                inline_tok = tokens[i + 1] if i + 1 < n else None
                children = (
                    inline_tok.children
                    if inline_tok is not None and inline_tok.type == "inline"
                    else []
                )
                text = _render_math_passthrough(_render_inline(children or []))
                lines.extend(text.split("\n"))
                i += 3
            elif ttype == "heading_open":
                try:
                    level = int((tok.tag or "h1")[1])
                except (ValueError, IndexError):
                    level = 1
                inline_tok = tokens[i + 1] if i + 1 < n else None
                children = (
                    inline_tok.children
                    if inline_tok is not None and inline_tok.type == "inline"
                    else []
                )
                if level <= 1:
                    styled = _render_inline(children or [], outer=(BOLD, UNDERLINE))
                else:
                    styled = _render_inline(children or [], outer=(BOLD,))
                lines.extend(styled.split("\n"))
                i += 3
            elif ttype == "blockquote_open":
                j = self._find_close(tokens, i, "blockquote_open", "blockquote_close")
                inner = self.render_blocks(tokens[i + 1 : j])
                prefix = f"{GRAY}\u2502{RESET} "
                for line in inner:
                    lines.append(f"{prefix}{line}" if line else f"{prefix}".rstrip())
                i = j + 1
            elif ttype in ("bullet_list_open", "ordered_list_open"):
                close_type = (
                    "bullet_list_close" if ttype == "bullet_list_open" else "ordered_list_close"
                )
                j = self._find_close(tokens, i, ttype, close_type)
                lines.extend(
                    self._render_list(tokens[i + 1 : j], ordered=(ttype == "ordered_list_open"))
                )
                i = j + 1
            elif ttype == "fence":
                lines.extend(self._render_fence(tok.info or "", tok.content or ""))
                i += 1
            elif ttype == "code_block":
                lines.extend(self._render_fence("", tok.content or ""))
                i += 1
            elif ttype == "hr":
                lines.append(f"{GRAY}{'─' * HR_WIDTH}{RESET}")
                i += 1
            elif ttype == "table_open":
                j = self._find_close(tokens, i, "table_open", "table_close")
                lines.extend(self._render_table(tokens[i + 1 : j]))
                i = j + 1
            elif ttype == "html_block":
                content = (tok.content or "").rstrip("\n")
                lines.extend(content.split("\n") if content else [])
                i += 1
            else:
                # Skip standalone closing tokens / references already
                # consumed by their parents; never crash on unknown blocks.
                i += 1
        return lines

    @staticmethod
    def _find_close(tokens: list, start: int, open_type: str, close_type: str) -> int:
        depth = 0
        for k in range(start, len(tokens)):
            if tokens[k].type == open_type:
                depth += 1
            elif tokens[k].type == close_type:
                depth -= 1
                if depth == 0:
                    return k
        return len(tokens) - 1

    def _render_list(self, tokens: list, ordered: bool) -> list[str]:
        lines: list[str] = []
        # Collect items between list_item_open / list_item_close.
        items: list[list] = []
        k = 0
        start_num = 1
        first = True
        while k < len(tokens):
            if tokens[k].type == "list_item_open":
                info = getattr(tokens[k], "info", "") or ""
                if first and ordered and str(info).strip().isdigit():
                    start_num = int(str(info).strip())
                    first = False
                depth = 1
                m = k + 1
                while m < len(tokens):
                    if tokens[m].type == "list_item_open":
                        depth += 1
                    elif tokens[m].type == "list_item_close":
                        depth -= 1
                        if depth == 0:
                            break
                    m += 1
                items.append(tokens[k + 1 : m])
                k = m + 1
            else:
                k += 1
        number = start_num
        for item_tokens in items:
            if ordered:
                prefix = f"{number}. "
                number += 1
            else:
                prefix = f"{BULLET} "
            inner = self.render_blocks(item_tokens)
            text = "\n".join(inner) if inner else ""
            item_lines = text.split("\n") if text else [""]
            pad = " " * _visible_width(prefix)
            lines.append(f"{prefix}{item_lines[0]}".rstrip())
            for cont in item_lines[1:]:
                lines.append(f"{pad}{cont}" if cont else "")
        return lines

    @staticmethod
    def _render_fence(info: str, content: str) -> list[str]:
        lang = info.strip().split()[0] if info.strip() else ""
        header = f"── {lang} ──" if lang else "────────"
        code_lines = content.split("\n")
        if code_lines and code_lines[-1] == "":
            code_lines.pop()
        footer = "─" * _visible_width(header)
        return [f"{GRAY}{header}{RESET}", *code_lines, f"{GRAY}{footer}{RESET}"]

    def _render_table(self, tokens: list) -> list[str]:
        rows: list[tuple[list[tuple[str, str]], bool]] = []
        i = 0
        n = len(tokens)
        while i < n:
            tok = tokens[i]
            if tok.type == "tr_open":
                # Find matching tr_close.
                depth = 1
                m = i + 1
                while m < n:
                    if tokens[m].type == "tr_open":
                        depth += 1
                    elif tokens[m].type == "tr_close":
                        depth -= 1
                        if depth == 0:
                            break
                    m += 1
                cells: list[tuple[str, str]] = []
                is_header = False
                k = i + 1
                while k < m:
                    if tokens[k].type in ("th_open", "td_open"):
                        is_header = is_header or tokens[k].type == "th_open"
                        align = _parse_align(getattr(tokens[k], "attrs", None))
                        inline_children: list = []
                        if k + 1 < m and tokens[k + 1].type == "inline":
                            inline_children = tokens[k + 1].children or []
                        cell_text = _render_inline(inline_children).replace("\n", " ")
                        if tokens[k].type == "th_open":
                            # Header cells are additionally bold.
                            hdr = _InlineRenderer()
                            hdr.open(BOLD)
                            hdr.feed(inline_children)
                            hdr.close()
                            cell_text = hdr.value().replace("\n", " ")
                        cells.append((cell_text, align))
                    k += 1
                rows.append((cells, is_header))
                i = m + 1
            else:
                i += 1
        if not rows:
            return []
        col_count = max(len(cells) for cells, _ in rows)
        widths = [0] * col_count
        for cells, _ in rows:
            for idx in range(col_count):
                text = cells[idx][0] if idx < len(cells) else ""
                widths[idx] = max(widths[idx], _visible_width(text))

        def border(left: str, mid: str, right: str) -> str:
            parts = ["─" * (w + 2) for w in widths]
            return f"{GRAY}{left}{mid.join(parts)}{right}{RESET}"

        def row_line(cells: list[tuple[str, str]]) -> str:
            sep = f"{GRAY}│{RESET}"
            out_cells = []
            for idx in range(col_count):
                text, align = cells[idx] if idx < len(cells) else ("", "left")
                out_cells.append(f" {_pad_cell(text, widths[idx], align)} ")
            return f"{sep}{sep.join(out_cells)}{sep}"

        lines = [border("┌", "┬", "┐")]
        header_done = False
        for cells, is_header in rows:
            lines.append(row_line(cells))
            if is_header and not header_done:
                lines.append(border("├", "┼", "┤"))
                header_done = True
        lines.append(border("└", "┴", "┘"))
        return lines


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def render(text: str) -> str:
    """Render Markdown *text* into an ANSI-styled terminal string.

    Args:
        text: Markdown source. May already contain ANSI codes (e.g. from
            ``mukimov.color``) — they are preserved, not removed.

    Returns:
        The rendered string with ANSI styles. Ends with RESET when any
        styling was applied, so the terminal always returns to normal.

    Raises:
        TypeError: If *text* is not a string.
    """
    if not isinstance(text, str):
        raise TypeError(f"markdown.render() expected str, got {type(text).__name__}")
    if text == "":
        return ""
    leading, core, trailing = _split_boundary_ansi(text)
    protected, saved = _protect_ansi(core)
    tokens = _parser.parse(protected)
    lines = _BlockRenderer().render_blocks(tokens)
    out = "\n".join(lines)
    out = _restore_ansi(out, saved)
    out = f"{leading}{out}{trailing}"
    if out and "\x1b" in out and not out.endswith(RESET):
        out += RESET
    return out


def print(text: str) -> None:  # noqa: A001 - public API name is intentional
    """Render Markdown *text* and print it to the terminal.

    Args:
        text: Markdown source (same input as :func:`render`).

    Raises:
        TypeError: If *text* is not a string.
    """
    if not isinstance(text, str):
        raise TypeError(f"markdown.print() expected str, got {type(text).__name__}")
    builtins.print(render(text))
