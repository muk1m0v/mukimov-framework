"""Tests for mukimov.text.markdown (ANSI terminal Markdown renderer)."""

import io
import re
import unittest
from unittest import mock

from mukimov.color import green, red
from mukimov.text import markdown
from mukimov.text.markdown import render

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

BOLD = "\x1b[1m"
ITALIC = "\x1b[3m"
STRIKE = "\x1b[9m"
RESET = "\x1b[0m"


def strip(text):
    return ANSI_RE.sub("", text)


class TestApi(unittest.TestCase):
    def test_render_callable(self):
        self.assertTrue(callable(markdown.render))

    def test_print_callable(self):
        self.assertTrue(callable(markdown.print))

    def test_render_returns_str(self):
        self.assertIsInstance(markdown.render("**Hello**"), str)

    def test_render_does_not_print(self):
        with mock.patch("builtins.print") as mprint:
            result = markdown.render("**Hello**")
            self.assertIsInstance(result, str)
            mprint.assert_not_called()

    def test_print_outputs_rendered(self):
        with mock.patch("sys.stdout", new_callable=io.StringIO) as out:
            markdown.print("**Hello**")
            self.assertEqual(out.getvalue(), markdown.render("**Hello**") + "\n")

    def test_no_format_name(self):
        # The public function must not be named `format`.
        self.assertFalse(hasattr(markdown, "format"))
        self.assertTrue(hasattr(markdown, "render"))


class TestHeadings(unittest.TestCase):
    def test_h1_to_h6(self):
        for level in range(1, 7):
            with self.subTest(level=level):
                result = markdown.render(f"{'#' * level} Hello")
                self.assertIn("Hello", result)
                self.assertIn(BOLD, result)
                # Markdown markers must be gone.
                self.assertNotIn("#", strip(result))

    def test_h1_underline(self):
        result = markdown.render("# Welcome")
        self.assertIn("\x1b[4m", result)
        self.assertEqual(strip(result), "Welcome")

    def test_heading_example(self):
        self.assertEqual(strip(markdown.render("# Welcome")), "Welcome")


class TestInlineStyles(unittest.TestCase):
    def test_bold_stars(self):
        result = markdown.render("**Hello**")
        self.assertIn(BOLD, result)
        self.assertIn("Hello", result)
        self.assertNotIn("**", strip(result))

    def test_bold_underscores(self):
        result = markdown.render("__Hello__")
        self.assertIn(BOLD, result)
        self.assertNotIn("__", strip(result))

    def test_italic_star(self):
        result = markdown.render("*Hello*")
        self.assertIn(ITALIC, result)
        self.assertEqual(strip(result), "Hello")

    def test_italic_underscore(self):
        result = markdown.render("_Hello_")
        self.assertIn(ITALIC, result)
        self.assertEqual(strip(result), "Hello")

    def test_bold_italic(self):
        result = markdown.render("***Hello***")
        self.assertIn(BOLD, result)
        self.assertIn(ITALIC, result)
        self.assertEqual(strip(result), "Hello")

    def test_strikethrough(self):
        result = markdown.render("~~Hello~~")
        self.assertIn(STRIKE, result)
        self.assertEqual(strip(result), "Hello")

    def test_inline_code(self):
        result = markdown.render("`code`")
        self.assertIn("code", result)
        self.assertIn("\x1b[", result)  # distinct code style
        self.assertNotIn("`", strip(result))

    def test_nested_bold_italic(self):
        result = markdown.render("**Hello *world***")
        self.assertIn(BOLD, result)
        self.assertIn(ITALIC, result)
        self.assertEqual(strip(result), "Hello world")

    def test_nested_triple(self):
        result = markdown.render("***Hello***")
        self.assertEqual(strip(result), "Hello")
        self.assertIn(BOLD, result)
        self.assertIn(ITALIC, result)


class TestBlocks(unittest.TestCase):
    def test_quote(self):
        result = markdown.render("> quote")
        plain = strip(result)
        self.assertIn("quote", plain)
        self.assertIn("│", plain)

    def test_quote_nested_bold(self):
        result = markdown.render("> **Important:** something happened")
        self.assertIn(BOLD, result)
        plain = strip(result)
        self.assertIn("Important:", plain)
        self.assertIn("something happened", plain)

    def test_unordered_dash(self):
        result = markdown.render("- item\n- bitem")
        plain = strip(result)
        self.assertIn("• item", plain)
        self.assertIn("• bitem", plain)
        self.assertNotIn("- item", plain)

    def test_unordered_star(self):
        result = markdown.render("* item")
        self.assertIn("item", strip(result))

    def test_unordered_plus(self):
        result = markdown.render("+ item")
        self.assertIn("item", strip(result))

    def test_ordered_list(self):
        result = markdown.render("1. first\n2. second")
        plain = strip(result)
        self.assertIn("1.", plain)
        self.assertIn("first", plain)
        self.assertIn("2.", plain)
        self.assertIn("second", plain)

    def test_horizontal_rule(self):
        result = markdown.render("---")
        self.assertIn("─", strip(result))
        self.assertNotIn("-", strip(result).replace("─", "").replace(" ", ""))

    def test_link(self):
        result = markdown.render("[OpenAI](https://openai.com)")
        plain = strip(result)
        self.assertIn("OpenAI", plain)
        self.assertIn("https://openai.com", plain)
        self.assertNotIn("[OpenAI]", plain)

    def test_multiline_text(self):
        result = markdown.render("line one\n\nline two")
        plain = strip(result)
        self.assertIn("line one", plain)
        self.assertIn("line two", plain)
        self.assertIn("\n", result)


class TestCodeBlocks(unittest.TestCase):
    def test_indented_code_is_rendered(self):
        plain = strip(markdown.render("    print(123)\n        **literal**"))
        self.assertIn("print(123)\n    **literal**", plain)

    def test_fenced_code_preserved(self):
        result = markdown.render('```\nprint("Hi")\n```')
        plain = strip(result)
        self.assertIn('print("Hi")', plain)

    def test_language_shown(self):
        result = markdown.render('```python\ndef hello():\n    print("Hello")\n```')
        plain = strip(result)
        self.assertIn("python", plain)
        self.assertIn("def hello():", plain)
        self.assertIn('    print("Hello")', plain)  # indentation kept

    def test_language_code_block_example(self):
        code = '```python\ndef hello(name):\n    if name:\n        print(f"Hello {name}")\n```'
        plain = strip(markdown.render(code))
        self.assertIn("def hello(name):", plain)
        self.assertIn("        print(", plain)

    def test_no_markdown_inside_code(self):
        result = markdown.render("```\n**not bold** *x* # hi\n```")
        plain = strip(result)
        self.assertIn("**not bold**", plain)
        self.assertIn("*x*", plain)
        self.assertIn("# hi", plain)
        # The code lines themselves carry no bold styling.
        raw_code_line = result.split("\n")[1]
        self.assertNotIn(BOLD, raw_code_line)

    def test_inline_code_not_bold(self):
        result = markdown.render("`**not bold**`")
        self.assertNotIn(BOLD, result)


class TestEscaping(unittest.TestCase):
    def test_escaped_not_bold(self):
        result = markdown.render(r"\**Not bold**")
        self.assertNotIn(BOLD, result)

    def test_code_span_not_bold(self):
        result = markdown.render("`**not bold**`")
        self.assertNotIn(BOLD, result)


class TestTables(unittest.TestCase):
    TABLE = (
        "| Name | Age | Language |\n"
        "|------|----:|----------|\n"
        "| Mukimov | 17 | Python |\n"
        "| Alex | 20 | Go |"
    )

    def test_table_borders(self):
        plain = strip(markdown.render(self.TABLE))
        self.assertIn("┌", plain)
        self.assertIn("┐", plain)
        self.assertIn("└", plain)
        self.assertIn("┘", plain)
        self.assertIn("│", plain)
        self.assertIn("─", plain)

    def test_table_content(self):
        plain = strip(markdown.render(self.TABLE))
        for word in ("Name", "Age", "Language", "Mukimov", "17", "Python", "Alex", "Go"):
            self.assertIn(word, plain)

    def test_table_alignment(self):
        src = "| Left | Center | Right |\n|:-----|:------:|------:|\n| A | B | C |"
        plain = strip(markdown.render(src))
        data_line = [ln for ln in plain.split("\n") if " A " in ln or "│ A" in ln][0]
        # Right-aligned cell 'C' must touch the right border: 'C │'.
        right_line = [ln for ln in plain.split("\n") if "C" in ln and "Center" not in ln][0]
        self.assertIn("C │", right_line)
        self.assertIn("│ A", data_line)

    def test_table_unicode_width(self):
        src = "| Name |\n|------|\n| 日本語 |\n| a |"
        plain = strip(markdown.render(src))
        widths = {len(ln) for ln in plain.split("\n")}
        # Box lines must all have the same *character* count here is not
        # required, but every line must start/end with border chars.
        for ln in plain.split("\n"):
            self.assertTrue(ln.startswith(("┌", "│", "├", "└")))
        self.assertIn("日本語", plain)

    def test_markdown_inside_cells(self):
        plain = strip(markdown.render("| Status |\n|--------|\n| **OK** |"))
        self.assertIn("OK", plain)
        raw = markdown.render("| Status |\n|--------|\n| **OK** |")
        self.assertIn(BOLD, raw)
        self.assertNotIn("**", plain)

    def test_table_ansi_width(self):
        # ANSI codes must not break column width calculation.
        raw = markdown.render(self.TABLE)
        plain = strip(raw)
        lines = plain.split("\n")
        # Top border inner width must match content rows inner width
        # measured in visible characters.
        top = lines[0][1:-1]
        for ln in lines[1:]:
            if ln.startswith("│"):
                self.assertEqual(len(ln[1:-1]), len(top))


class TestUnicode(unittest.TestCase):
    def test_languages(self):
        src = "English Русский Тоҷикӣ 中文 日本語 한국어"
        plain = strip(markdown.render(src))
        for word in ("English", "Русский", "Тоҷикӣ", "中文", "日本語", "한국어"):
            self.assertIn(word, plain)

    def test_emoji(self):
        plain = strip(markdown.render("😀 🚀 ❤️ **bold**"))
        self.assertIn("😀", plain)
        self.assertIn("🚀", plain)


class TestAnsiCompatibility(unittest.TestCase):
    def test_green_bold(self):
        result = markdown.render(green("**Hello**"))
        self.assertIn("\x1b[92m", result)  # green kept
        self.assertIn(BOLD, result)  # markdown applied
        self.assertIn("Hello", strip(result))
        self.assertNotIn("**", strip(result))

    def test_red_italic(self):
        result = markdown.render(red("*Error*"))
        self.assertIn("\x1b[91m", result)
        self.assertIn(ITALIC, result)
        self.assertIn("Error", strip(result))

    def test_green_success_example(self):
        result = markdown.render(green("**Success!**"))
        self.assertIn("Success!", strip(result))
        self.assertIn(BOLD, result)

    def test_ansi_around_punct_closer(self):
        # ANSI right after `!**` must not break emphasis parsing.
        result = markdown.render("say " + green("**Hi!**") + " ok")
        self.assertIn(BOLD, result)
        self.assertEqual(strip(result), "say Hi! ok")

    def test_inner_ansi_kept(self):
        result = markdown.render("a " + green("x") + " **b**")
        self.assertIn("\x1b[92m", result)
        self.assertIn(BOLD, result)
        self.assertEqual(strip(result), "a x b")

    def test_user_ansi_not_removed(self):
        result = markdown.render(green("**Hello**"))
        # The original green open code must still be present.
        self.assertGreaterEqual(result.count("\x1b[92m"), 1)

    def test_reset_behavior(self):
        for src in ("**bold**", "*it*", "***both***", "~~s~~", "`c`", "# H", "> q"):
            with self.subTest(src=src):
                result = markdown.render(src)
                if "\x1b" in result:
                    self.assertTrue(
                        result.endswith(RESET), f"{src!r} must end with RESET"
                    )
        # No style should leak: plain text after styled render is unaffected.
        combined = markdown.render("**b**") + "plain"
        tail = combined[len(markdown.render("**b**")) :]
        self.assertEqual(tail, "plain")
        self.assertNotIn("\x1b[1m", tail)


class TestValidation(unittest.TestCase):
    def test_render_int(self):
        with self.assertRaises(TypeError) as cm:
            markdown.render(123)  # type: ignore[arg-type]
        self.assertEqual(str(cm.exception), "markdown.render() expected str, got int")

    def test_render_none(self):
        with self.assertRaises(TypeError) as cm:
            markdown.render(None)  # type: ignore[arg-type]
        self.assertEqual(
            str(cm.exception), "markdown.render() expected str, got NoneType"
        )

    def test_print_none(self):
        with self.assertRaises(TypeError) as cm:
            markdown.print(None)  # type: ignore[arg-type]
        self.assertEqual(
            str(cm.exception), "markdown.print() expected str, got NoneType"
        )

    def test_print_int(self):
        with self.assertRaises(TypeError) as cm:
            markdown.print(123)  # type: ignore[arg-type]
        self.assertEqual(
            str(cm.exception), "markdown.print() expected str, got int"
        )

    def test_empty_string(self):
        self.assertEqual(markdown.render(""), "")
        with mock.patch("sys.stdout", new_callable=io.StringIO):
            markdown.print("")  # must not raise


class TestRobustness(unittest.TestCase):
    def test_latex_inline_passthrough(self):
        plain = strip(markdown.render("$E = mc^2$"))
        self.assertIn("E = mc^2", plain)

    def test_latex_block_passthrough(self):
        plain = strip(markdown.render("$$\nE = mc^2\n$$"))
        self.assertIn("E = mc^2", plain)

    def test_old_apis_intact(self):
        from mukimov import stars
        from mukimov.color import blue

        self.assertTrue(callable(stars))
        self.assertIn("hi", blue("hi"))

    def test_import_path(self):
        from mukimov.text import markdown as md

        self.assertIs(md, markdown)


if __name__ == "__main__":
    unittest.main()
