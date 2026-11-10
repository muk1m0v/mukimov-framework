from contextlib import redirect_stderr, redirect_stdout
from io import BytesIO, StringIO
from pathlib import Path
from runpy import run_path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import ANY, MagicMock, patch
from urllib.parse import urlencode
from wsgiref.util import setup_testing_defaults

from mukimov import __version__
from mukimov._startweb import main as startweb
from mukimov.web import App, abort, redirect, render_template, request


class TestWeb(TestCase):
    def setUp(self):
        folder = TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.app = App(root=self.root)

    def call(self, path="/", method="GET", body=b"", **overrides):
        environ = {}
        setup_testing_defaults(environ)
        environ.update(PATH_INFO=path, REQUEST_METHOD=method, CONTENT_LENGTH=str(len(body)),
                       CONTENT_TYPE="application/x-www-form-urlencoded",
                       **{"wsgi.input": BytesIO(body), "wsgi.errors": StringIO()})
        environ.update(overrides)
        result = {}

        def start_response(status, headers):
            result.update(status=int(status.split()[0]), headers=dict(headers))

        data = b"".join(self.app(environ, start_response))
        return result["status"], result["headers"], data

    def test_post_form_escapes_html_and_custom_error_preserves_status(self):
        templates = self.root / "templates"
        templates.mkdir()
        (templates / "hello.html").write_text("<p>{{ name }}</p>", encoding="utf-8")

        @self.app.route("/hello", methods=["POST"])
        def hello():
            name = request.form.get("name", "").strip()
            if not name:
                abort(400)
            return render_template("hello.html", name=name)

        @self.app.errorhandler(400)
        def bad_request():
            return "<h1>Fill in your name</h1>"

        status, _, data = self.call("/hello", "POST", urlencode({"name": "<b>Али</b>"}).encode())
        self.assertEqual(status, 200)
        self.assertEqual(data.decode(), "<p>&lt;b&gt;Али&lt;/b&gt;</p>")
        for body, overrides in ((b"name=", {}), (b"name=%FF", {}),
                                (b"name=Sam", {"CONTENT_LENGTH": "invalid"})):
            with self.subTest(body=body, overrides=overrides):
                status, _, data = self.call("/hello", "POST", body, **overrides)
                self.assertEqual(status, 400)
                self.assertEqual(data, b"<h1>Fill in your name</h1>")

    def test_routing_returns_correct_status_for_head_and_wrong_method(self):
        @self.app.route("/")
        def home():
            return "home"

        @self.app.errorhandler(404)
        def not_found():
            return "custom 404"

        status, headers, body = self.call("/", "HEAD")
        self.assertEqual((status, headers["Content-Length"], body), (200, "4", b""))
        status, headers, _ = self.call("/", "POST")
        self.assertEqual((status, headers["Allow"]), (405, "GET, HEAD"))
        status, _, body = self.call("/missing")
        self.assertEqual((status, body), (404, b"custom 404"))

    def test_example_hello_opens_the_form_and_accepts_a_submission(self):
        from example.web.app import app

        self.app = app
        status, _, body = self.call("/hello")
        self.assertEqual(status, 200)
        self.assertIn(b'<form class="card" action="/hello" method="post">', body)
        self.assertNotIn(b'class="form-result"', body)
        status, headers, body = self.call("/hello", "POST", b"name=Ali")
        self.assertEqual((status, headers["Location"], body), (303, "/hello?name=Ali", b""))
        status, _, body = self.call("/hello", QUERY_STRING="name=Ali")
        self.assertEqual(status, 200)
        self.assertIn('<h2 class="form-result">Привет, Ali!</h2>'.encode(), body)
        self.assertEqual(self.call("/hello", "POST", b"name=")[0], 400)
        self.assertEqual(self.call("/hello", "PUT")[0], 405)
        self.assertEqual(self.call("/hello", "HEAD")[0], 200)

    def test_redirect_rejects_external_and_invalid_locations(self):
        for location in ("https://example.com", "//example.com", "/\\example.com", "/a\r\nX: bad"):
            with self.subTest(location=location), self.assertRaises(ValueError):
                redirect(location)

    def test_custom_template_tags_support_nesting_else_and_escaping(self):
        templates = self.root / "templates"
        templates.mkdir()
        (templates / "items.html").write_text(
            "{$ if title $}<h1>{{ title }}</h1>{$ elif items $}"
            "{$ for item in items $}{$ if item $}<li>{{ item }}</li>{$ overif $}"
            "{$ overfor $}{$ else $}Empty{$ overif $}",
            encoding="utf-8",
        )

        @self.app.route("/")
        def items():
            return render_template("items.html", items=["<b>one</b>", "", "two"])

        @self.app.route("/title")
        def title():
            return render_template("items.html", title="<em>Title</em>")

        @self.app.route("/empty")
        def empty():
            return render_template("items.html", items=[])

        self.assertEqual(self.call("/")[2], b"<li>&lt;b&gt;one&lt;/b&gt;</li><li>two</li>")
        self.assertEqual(self.call("/title")[2], b"<h1>&lt;em&gt;Title&lt;/em&gt;</h1>")
        self.assertEqual(self.call("/empty")[2], b"Empty")

    def test_custom_tags_preserve_jinja_raw_blocks_comments_and_quoted_text(self):
        templates = self.root / "templates"
        templates.mkdir()
        (templates / "mixed.html").write_text(
            '{% raw %}{$ if literal $}{% endraw %}'
            '{# {$ overif $} #}{{ "{$ overfor $}" }}'
            '{$ if marker == "$}" $}{% for item in items %}{{ item }}{% endfor %}{$ overif $}',
            encoding="utf-8",
        )

        @self.app.route("/")
        def mixed():
            return render_template("mixed.html", marker="$}", items=["one", "two"])

        self.assertEqual(self.call("/")[2], b"{$ if literal $}{$ overfor $}onetwo")

    def test_view_methods_also_work_inside_route_and_preserve_explicit_methods(self):
        @self.app.route("/explicit", methods=["GET"])
        @self.app.route("/view")
        @self.app.view(methods=["POST"])
        def handler():
            return request.method

        self.assertEqual(self.call("/view", "GET")[0], 405)
        self.assertEqual(self.call("/view", "POST")[2], b"POST")
        self.assertEqual(self.call("/explicit", "GET")[2], b"GET")
        self.assertEqual(self.call("/explicit", "POST")[0], 405)

    def test_conflicting_view_leaves_existing_routes_intact(self):
        @self.app.route("/hello", methods=["POST"])
        def submit():
            return "existing POST"

        @self.app.route("/hello")
        @self.app.route("/another")
        def home():
            return "existing GET"

        with self.assertRaises(ValueError):
            self.app.view(methods=["GET", "POST"])(home)

        self.assertEqual(self.call("/hello", "POST")[2], b"existing POST")
        self.assertEqual(self.call("/hello", "GET")[2], b"existing GET")
        self.assertEqual(self.call("/another", "POST")[0], 405)

    def test_static_types_and_private_paths(self):
        static = self.root / "static"
        static.mkdir()
        (self.root / ".env").write_bytes(b"private")
        (static / ".hidden").write_bytes(b"private")
        for name, content_type in (("style.css", "text/css"), ("app.js", "text/javascript"),
                                   ("logo.svg", "image/svg+xml")):
            (static / name).write_bytes(b"example")
            status, headers, body = self.call("/static/" + name)
            self.assertEqual((status, headers["Content-Type"], body), (200, content_type, b"example"))
        for path in ("/static", "/static/../.env", "/static/..\\.env", "/static/.hidden",
                     "/static/style.css:stream", "/static/missing.svg", "/.env"):
            self.assertEqual(self.call(path)[0], 404, path)

    def test_static_symlink_cannot_serve_an_outside_file(self):
        target = self.root / "private.txt"
        target.write_bytes(b"private")
        static = self.root / "static"
        static.mkdir()
        try:
            (static / "escape.txt").symlink_to(target)
        except (NotImplementedError, OSError):
            self.skipTest("The platform does not permit creating symlinks here")
        self.assertEqual(self.call("/static/escape.txt")[0], 404)

    def test_scaffold_uses_debug_pages_until_a_template_is_written(self):
        with patch("mukimov._startweb.Path.cwd", return_value=self.root), \
             redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            self.assertEqual(startweb(["demo-site"]), 0)
            self.assertEqual(startweb(["demo-site"]), 1)

        project = self.root / "demo-site"
        configuration = project / "core" / "conf.py"
        self.assertEqual(run_path(str(configuration))["BASE_DIR"], project.resolve())
        index = project / "templates" / "index.html"
        self.assertEqual(index.read_bytes(), b"")
        for category in ("css", "js", "img"):
            self.assertEqual(list((project / "content" / category).iterdir()), [])
        self.app = run_path(str(project / "app.py"))["app"]
        status, _, page = self.call()
        self.assertEqual(status, 200)
        self.assertIn("Сайт запущен".encode(), page)
        self.assertIn(b"DEBUG = True", page)
        index.unlink()
        self.assertIn(b"DEBUG = True", self.call()[2])

        index.write_text("<h1>My website</h1>", encoding="utf-8")
        self.assertEqual(self.call()[2], b"<h1>My website</h1>")
        (project / "content/css/style.css").write_text("body {}", encoding="utf-8")
        status, headers, body = self.call("/content/css/style.css")
        self.assertEqual((status, headers["Content-Type"], body), (200, "text/css", b"body {}"))
        (project / "content/css/private.txt").write_text("private", encoding="utf-8")
        self.assertEqual(self.call("/content/css/private.txt")[0], 404)
        self.assertEqual(self.call("/core/conf.py")[0], 404)

    def test_debug_error_pages_preserve_status_and_hide_exception_details(self):
        (self.root / "conf.py").write_text("DEBUG = True\n", encoding="utf-8")
        self.app = App(root=self.root)
        self.app.route("/bad")(lambda: abort(400))

        @self.app.route("/broken")
        def broken():
            raise RuntimeError("private details")

        for path, code in (("/bad", 400), ("/missing", 404), ("/broken", 500)):
            status, _, body = self.call(path)
            self.assertEqual(status, code)
            self.assertIn(b"DEBUG = True", body)
            self.assertNotIn(b"private details", body)

        (self.root / "conf.py").write_text("DEBUG = False\n", encoding="utf-8")
        self.app = App(root=self.root)
        self.app.route("/")(lambda: render_template("index.html"))
        (self.root / "templates").mkdir()
        (self.root / "templates" / "index.html").touch()
        self.assertEqual(self.call()[2], b"")
        status, _, body = self.call("/missing")
        self.assertEqual(status, 404)
        self.assertNotIn(b"DEBUG", body)

    def test_core_config_uses_project_root_and_custom_template_search_order(self):
        core = self.root / "core"
        core.mkdir()
        (self.root / "conf.py").write_text("raise RuntimeError('old config')", encoding="utf-8")
        (core / "conf.py").write_text(
            'from mukimov.dirs import BASE_DIR\n'
            'HTML_TEMPLATES = [BASE_DIR / "pages", "fallback"]\n',
            encoding="utf-8",
        )
        for folder, content in (("pages", "Primary"), ("fallback", "Fallback")):
            (self.root / folder).mkdir()
            (self.root / folder / "index.html").write_text(content, encoding="utf-8")
        self.app = App(root=self.root)
        self.app.route("/")(lambda: render_template("index.html"))
        self.assertEqual(self.call()[2], b"Primary")
        (self.root / "pages" / "index.html").unlink()
        self.assertEqual(self.call()[2], b"Fallback")

    def test_config_can_use_a_custom_path_or_disable_aliases(self):
        configuration = self.root / "conf.py"
        settings = 'CSS_SETTING = {"STYLE_MAIN_PATH": "/assets/styles/", "main style.css": "main_style"}\n'
        configuration.write_text(settings, encoding="utf-8")
        styles = self.root / "assets" / "styles"
        styles.mkdir(parents=True)
        (styles / "main style.css").write_bytes(b"body {}")
        templates = self.root / "templates"
        templates.mkdir()
        page = templates / "index.html"
        page.write_text('<link href="{$ \'main_style\' $}">', encoding="utf-8")

        self.app = App(root=self.root)
        self.app.route("/")(lambda: render_template("index.html"))
        self.assertIn(b'"/assets/styles/main%20style.css"', self.call()[2])
        self.assertEqual(self.call("/assets/styles/main style.css")[2], b"body {}")

        configuration.write_text("ALL_CONTENT_STATIC = False\n" + settings, encoding="utf-8")
        page.write_text('<link href="/assets/styles/main%20style.css">', encoding="utf-8")
        self.app = App(root=self.root)
        self.app.route("/")(lambda: render_template("index.html"))
        self.assertIn(b'"/assets/styles/main%20style.css"', self.call()[2])
        self.assertEqual(self.call("/assets/styles/main style.css")[0], 200)

    def test_content_config_rejects_paths_outside_the_project_and_duplicate_aliases(self):
        conf = self.root / "conf.py"
        conf.write_text('CSS_SETTING = {"STYLE_MAIN_PATH": "/../private/"}', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "STYLE_MAIN_PATH"):
            App(root=self.root)
        conf.write_text('CSS_SETTING = {"a.css": "main"}\nJAVASCRIPT_SETTING = {"a.js": "main"}',
                        encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Duplicate content alias"):
            App(root=self.root)

    def test_server_reports_bound_port_and_stops_on_interrupt(self):
        for platform, shortcut in (("win32", "Ctrl + C"), ("linux", "Ctrl + C"),
                                   ("darwin", "Control (⌃) + C")):
            with self.subTest(platform=platform):
                server = MagicMock()
                server.server_port = 9000
                server.serve_forever.side_effect = KeyboardInterrupt
                with patch("mukimov.web.sys.platform", platform), \
                     patch("mukimov.web.make_server", return_value=server) as start, \
                     redirect_stdout(StringIO()) as output:
                    self.app.run(port=9000, reload=False)
                start.assert_called_once_with("127.0.0.1", 9000, self.app, server_class=ANY)
                self.assertEqual(output.getvalue().splitlines(), [
                    "\x1b[92mСервер запущен: http://127.0.0.1:9000\x1b[0m",
                    f"\x1b[94mЧтобы остановить сервер, используйте комбинацию: {shortcut}\x1b[0m",
                    f"\x1b[94mMukimov Web Control - v{__version__}\x1b[0m",
                ])
                server.__exit__.assert_called_once()

    def test_failed_bind_uses_default_port_and_prints_only_an_error(self):
        with patch("mukimov.web.make_server", side_effect=OSError("busy")) as start, \
             redirect_stdout(StringIO()) as output, redirect_stderr(StringIO()) as errors:
            with self.assertRaises(SystemExit) as caught:
                self.app.run(reload=False)
        start.assert_called_once_with("127.0.0.1", 8000, self.app, server_class=ANY)
        self.assertEqual(caught.exception.code, 1)
        self.assertEqual(output.getvalue(), "")
        self.assertIn("8000", errors.getvalue())

    def test_run_enables_the_reloader_by_default(self):
        with patch("mukimov.web.supervise", return_value=True) as reload, \
             patch("mukimov.web.make_server") as start:
            self.app.run()
        reload.assert_called_once_with(self.root.resolve())
        start.assert_not_called()
