"""``mukimov.text`` — text renderers for the terminal.

Since ``mukimov 0.1.6`` this package provides a Markdown renderer:

```python
from mukimov.text import markdown

markdown.print("# Hello")
markdown.print("**Bold text**")
```

Only the terminal (ANSI) renderer lives here. Markdown parsing itself is
delegated to the small, stable ``markdown-it-py`` dependency — this package
never tries to re-implement Markdown parsing with fragile regular
expressions.
"""
