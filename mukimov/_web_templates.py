"""Translate mukimov control tags before Jinja parses a template."""

import re

from jinja2.ext import Extension

from ._web_content import ALIAS_PATTERN

# A closing delimiter inside a quoted expression is part of the expression.
_EXPRESSION_CHAR = r"""(?:"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'|[^"'])"""
_TEMPLATE_TAG = re.compile(
    r"\{%[-+]?\s*raw\s*[-+]?%\}.*?\{%[-+]?\s*endraw\s*[-+]?%\}"
    r"|\{#.*?#\}"
    rf"|\{{\{{{_EXPRESSION_CHAR}*?\}}\}}"
    rf"|\{{%{_EXPRESSION_CHAR}*?%\}}"
    rf"|\{{\$(?=\s*(?:if|elif|else|for|overif|overfor)\b)"
    rf"(?P<statement>{_EXPRESSION_CHAR}*?)\$\}}"
    rf"|\{{\$\s*(?P<quote>['\"])(?P<alias>{ALIAS_PATTERN})(?P=quote)\s*\$\}}",
    re.DOTALL,
)
_CLOSING_TAGS = {"overif": "endif", "overfor": "endfor"}


def _translate_tag(match: re.Match, *, assets_enabled: bool) -> str:
    alias = match.group("alias")
    if alias is not None and assets_enabled:
        return '{{ mukimov_asset_url("' + alias + '") }}'
    statement = match.group("statement")
    if statement is None:
        return match.group()
    alias = statement.strip()
    if alias in _CLOSING_TAGS:
        statement = statement.replace(alias, _CLOSING_TAGS[alias], 1)
    return "{%" + statement + "%}"


class ControlTags(Extension):
    def preprocess(self, source, name, filename=None):
        if "{$" not in source:
            return source
        assets_enabled = "mukimov_asset_url" in self.environment.globals
        return _TEMPLATE_TAG.sub(lambda match: _translate_tag(match, assets_enabled=assets_enabled), source)
