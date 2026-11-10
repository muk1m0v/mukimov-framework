"""A small WSGI app with HTML templates and a local development server."""

from __future__ import annotations

from contextvars import ContextVar
from functools import cached_property
from http import HTTPStatus
from pathlib import Path
from typing import NamedTuple
from typing import NoReturn
from urllib.parse import parse_qsl
from wsgiref.simple_server import WSGIServer, make_server
import mimetypes
import os
import socket
import sys
import traceback

from jinja2 import Environment, FileSystemLoader

from . import __version__
from .color import blue, green, red
from ._web_content import asset_parts, load_content
from ._web_reload import BIND_FAILED, WORKER_ENV, supervise
from ._web_templates import ControlTags

__all__ = ["App", "abort", "redirect", "render_template", "request"]

_ASSET_TYPES = {".css": "text/css", ".js": "text/javascript", ".mjs": "text/javascript", ".svg": "image/svg+xml"}
_HTML = "text/html; charset=utf-8"
_MAX_FORM_BYTES = 1024 * 1024
_DEFAULT_METHODS = ("GET",)


class _LocalServer(WSGIServer):
    def server_bind(self) -> None:
        if sys.platform == "win32":
            # Winsock's SO_REUSEADDR can take over an already bound port.
            self.allow_reuse_address = False
            if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


class _HTTPError(Exception):
    def __init__(self, status: HTTPStatus, *, allow: str = "") -> None:
        super().__init__(status.phrase)
        self.status = status
        self.allow = allow


class _Redirect(NamedTuple):
    location: str


def redirect(location: str) -> _Redirect:
    """Return a 303 See Other response for a local URL."""
    if (not isinstance(location, str) or not location.startswith("/") or location.startswith("//")
            or any(not 33 <= ord(char) <= 126 or char == "\\" for char in location)):
        raise ValueError("redirect() requires a local URL with percent-encoded special characters.")
    return _Redirect(location)


def abort(status: int) -> NoReturn:
    """Stop the current request with a standard HTTP error status."""
    code = HTTPStatus(status)
    if code < 400:
        raise ValueError("abort() requires a 4xx or 5xx status")
    raise _HTTPError(code)


class _Request:
    def __init__(self, app: App, environ: dict) -> None:
        self.app = app
        self.environ = environ

    @cached_property
    def form(self) -> dict[str, str]:
        """Parse a URL-encoded form when the handler first accesses it."""
        try:
            length = int(self.environ.get("CONTENT_LENGTH") or "0")
        except ValueError:
            abort(400)
        if not 0 <= length <= _MAX_FORM_BYTES:
            abort(400)
        if not length:
            return {}

        content_type = self.environ.get("CONTENT_TYPE", "").split(";", 1)[0].strip().lower()
        if content_type != "application/x-www-form-urlencoded":
            abort(400)
        body = self.environ["wsgi.input"].read(length)
        if len(body) != length:
            abort(400)
        try:
            return dict(parse_qsl(body.decode("utf-8"), keep_blank_values=True,
                                  strict_parsing=True, errors="strict", max_num_fields=1000))
        except ValueError:
            abort(400)


_active_request: ContextVar[_Request] = ContextVar("mukimov_web_request")


def _current_request() -> _Request:
    try:
        return _active_request.get()
    except LookupError:
        raise RuntimeError("This helper must be called inside a request handler.") from None


class _RequestProxy:
    @property
    def method(self) -> str:
        """The method dispatched to the handler. HEAD uses the GET handler."""
        method = _current_request().environ["REQUEST_METHOD"]
        return "GET" if method == "HEAD" else method

    @property
    def form(self) -> dict[str, str]:
        return _current_request().form

    @property
    def query(self) -> dict[str, str]:
        """Return URL query parameters."""
        query = _current_request().environ.get("QUERY_STRING", "")
        try:
            return dict(parse_qsl(query, keep_blank_values=True, max_num_fields=1000))
        except ValueError:
            abort(400)


request = _RequestProxy()


def render_template(template_name: str, /, **context) -> str:
    """Render a template from the current app's templates directory."""
    return _current_request().app._templates.get_template(template_name).render(**context)


def _route_methods(methods) -> tuple[str, ...]:
    methods = tuple(dict.fromkeys(method.upper() for method in methods))
    if not methods or set(methods) - {"GET", "POST"}:
        raise ValueError("Routes support GET and POST.")
    return methods


class App:
    """Serve exact-path GET and POST routes and files from static/."""

    def __init__(self, *, root: str | Path | None = None) -> None:
        if root is None:
            caller_file = sys._getframe(1).f_globals.get("__file__")
            root = Path(caller_file).resolve().parent if caller_file else Path.cwd()
        root = Path(root).resolve()
        self._root = root
        self._mounts, aliases = load_content(root)
        self._templates = Environment(
            loader=FileSystemLoader(root / "templates"), autoescape=True, extensions=[ControlTags]
        )
        if aliases is not None:
            self._templates.globals["mukimov_asset_url"] = aliases.__getitem__
        self._routes = {}
        self._default_routes = {}
        self._view_methods = {}
        self._error_handlers = {}

    def route(self, path: str, *, methods=None):
        """Register a handler for an exact URL path."""
        if not path.startswith("/") or "?" in path or "#" in path:
            raise ValueError("A route must be an absolute path without a query or fragment.")
        if self._asset_prefix(path):
            raise ValueError(f"{path} is reserved for asset files.")
        explicit = _route_methods(methods) if methods is not None else None

        def register(handler):
            methods = explicit or self._view_methods.get(handler, _DEFAULT_METHODS)
            routes = self._routes.setdefault(path, {})
            if routes.keys() & set(methods):
                raise ValueError(f"A handler already exists for {path} and these methods.")
            routes.update(dict.fromkeys(methods, handler))
            if explicit is None:
                self._default_routes.setdefault(handler, set()).add(path)
            return handler

        return register

    def view(self, *, methods):
        """Set methods for this handler's routes that omit `methods`."""
        methods = _route_methods(methods)

        def register(handler):
            previous = self._view_methods.get(handler, _DEFAULT_METHODS)
            paths = self._default_routes.get(handler, ())
            for path in paths:
                other_methods = self._routes[path].keys() - set(previous)
                if other_methods.intersection(methods):
                    raise ValueError(f"A handler already exists for {path} and these methods.")
            for path in paths:
                routes = self._routes[path]
                for method in previous:
                    del routes[method]
                routes.update(dict.fromkeys(methods, handler))
            self._view_methods[handler] = methods
            return handler

        return register

    def errorhandler(self, status: int):
        """Register a page renderer without changing the HTTP error status."""
        code = HTTPStatus(status)
        if code < 400:
            raise ValueError("errorhandler() requires a 4xx or 5xx status")

        def register(handler):
            self._error_handlers[code] = handler
            return handler

        return register

    def _asset_prefix(self, path: str):
        return next((prefix for prefix in self._mounts
                     if path == prefix[:-1] or path.startswith(prefix)), None)

    def _asset(self, prefix: str, name: str) -> tuple[bytes, str]:
        directory, extensions = self._mounts[prefix]
        try:
            parts = asset_parts(name)
            root = directory.resolve()
            if root != directory:
                abort(404)
            path = root.joinpath(*parts).resolve()
            relative = path.relative_to(root)
            if any(part.startswith(".") for part in relative.parts) or not path.is_file():
                abort(404)
            if extensions is not None and (
                path.suffix.lower() not in extensions or Path(name).suffix.lower() not in extensions
            ):
                abort(404)
            content = path.read_bytes()
        except (OSError, ValueError, RuntimeError):
            abort(404)
        content_type = _ASSET_TYPES.get(path.suffix.lower()) or mimetypes.guess_type(path.name)[0]
        return content, content_type or "application/octet-stream"

    def _dispatch(self, environ: dict) -> tuple[bytes, str] | _Redirect:
        method = environ["REQUEST_METHOD"]
        path = environ["PATH_INFO"].encode("latin-1").decode("utf-8", errors="replace") or "/"
        prefix = self._asset_prefix(path)
        if prefix:
            if method not in ("GET", "HEAD"):
                raise _HTTPError(HTTPStatus.METHOD_NOT_ALLOWED, allow="GET, HEAD")
            return self._asset(prefix, path[len(prefix):])
        routes = self._routes.get(path)
        if routes is None:
            abort(404)
        handler = routes.get("GET" if method == "HEAD" else method)
        if handler is None:
            allowed = sorted(routes.keys() | ({"HEAD"} if "GET" in routes else set()))
            raise _HTTPError(HTTPStatus.METHOD_NOT_ALLOWED, allow=", ".join(allowed))
        result = handler()
        if isinstance(result, _Redirect):
            return result
        return result.encode("utf-8"), _HTML

    @staticmethod
    def _default_error(status: HTTPStatus) -> bytes:
        title = f"{status.value} {status.phrase}"
        return f'<!doctype html><meta charset="utf-8"><title>{title}</title><h1>{title}</h1>'.encode("utf-8")

    def _response(self, environ: dict) -> tuple[HTTPStatus, bytes, str, tuple]:
        try:
            try:
                result = self._dispatch(environ)
                if isinstance(result, _Redirect):
                    return HTTPStatus.SEE_OTHER, b"", _HTML, (("Location", result.location),)
                body, content_type = result
                return HTTPStatus.OK, body, content_type, ()
            except _HTTPError as error:
                handler = self._error_handlers.get(error.status)
                body = handler().encode("utf-8") if handler else self._default_error(error.status)
                headers = (("Allow", error.allow),) if error.allow else ()
                return error.status, body, _HTML, headers
        except Exception:
            traceback.print_exc(file=environ["wsgi.errors"])
            status = HTTPStatus.INTERNAL_SERVER_ERROR
            return status, self._default_error(status), _HTML, ()

    def __call__(self, environ, start_response):
        token = _active_request.set(_Request(self, environ))
        try:
            status, body, content_type, extra_headers = self._response(environ)
        finally:
            _active_request.reset(token)
        headers = [
            ("Content-Type", content_type),
            ("Content-Length", str(len(body))),
            ("X-Content-Type-Options", "nosniff"),
            *extra_headers,
        ]
        start_response(f"{status.value} {status.phrase}", headers)
        return [] if environ["REQUEST_METHOD"] == "HEAD" else [body]

    def run(self, *, port: int = 8000, reload: bool = True) -> None:
        """Run the development server and restart after Python source changes."""
        if reload and supervise(self._root):
            return
        host = "127.0.0.1"
        try:
            server = make_server(host, port, self, server_class=_LocalServer)
        except OSError as error:
            print(red(f"Не удалось запустить сервер на порту {port}: {error}"),
                  file=sys.stderr, flush=True)
            status = BIND_FAILED if os.environ.get(WORKER_ENV) == "1" else 1
            raise SystemExit(status) from None

        with server:
            print(green(f"Сервер запущен: http://{host}:{server.server_port}"), flush=True)
            shortcut = "Control (⌃) + C" if sys.platform == "darwin" else "Ctrl + C"
            print(blue(f"Чтобы остановить сервер, используйте комбинацию: {shortcut}"), flush=True)
            print(blue(f"Mukimov Web Control - v{__version__}"), flush=True)
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass
