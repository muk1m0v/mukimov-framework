"""Exercise the installed wheel over HTTP and verify development reloading."""

from http.client import HTTPConnection, HTTPException
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urlencode
import os
import shutil
import signal
import socket
import subprocess
import sys
import time


def fetch(port, path, method="GET", form=None):
    client = HTTPConnection("127.0.0.1", port, timeout=2)
    try:
        body = urlencode(form).encode() if form is not None else None
        headers = {"Content-Type": "application/x-www-form-urlencoded"} if body else {}
        client.request(method, path, body=body, headers=headers)
        response = client.getresponse()
        return response.status, response.getheader("Location"), response.read().decode("utf-8")
    finally:
        client.close()


def wait_for_page(process, port, text):
    deadline = time.monotonic() + 20
    last_result = "No response yet"
    while time.monotonic() < deadline and process.poll() is None:
        try:
            status, _, body = fetch(port, "/")
            if status == 200 and text in body:
                return
            last_result = f"HTTP {status}"
        except (OSError, HTTPException) as error:
            last_result = str(error)
        time.sleep(0.1)
    raise AssertionError(f"The example did not serve {text!r}: {last_result}; exit={process.poll()}")


def stop(process):
    if process.poll() is None:
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        else:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
    process.wait(timeout=10)


def main():
    example = Path(__file__).resolve().parents[1] / "example" / "web"
    with TemporaryDirectory() as folder:
        project = Path(folder) / "web"
        shutil.copytree(example, project, ignore=shutil.ignore_patterns("__pycache__"))
        starter = Path(folder) / "starter"
        starter.mkdir()
        subprocess.run([sys.executable, "-m", "mukimov", "startweb"],
                       cwd=starter, check=True)
        assert (starter / "app.py").is_file()
        assert (starter / "core" / "conf.py").is_file()
        assert (starter / "templates" / "index.html").read_bytes() == b""
        with socket.socket() as reservation:
            reservation.bind(("127.0.0.1", 0))
            port = reservation.getsockname()[1]
        environment = dict(os.environ, MUKIMOV_WEB_PORT=str(port), PYTHONIOENCODING="cp1252")
        with subprocess.Popen([sys.executable, "app.py"],
                              cwd=project, env=environment, start_new_session=os.name != "nt") as process:
            try:
                wait_for_page(process, port, "Мукимов")
                status, location, _ = fetch(port, "/hello", "POST", {"name": "Тест"})
                assert status == 303 and location.startswith("/hello?")
                for _ in range(2):
                    status, _, body = fetch(port, location)
                    assert status == 200 and "Привет, Тест!" in body
                assert fetch(port, "/hello", "POST", {"name": ""})[0] == 400
                assert fetch(port, "/static/css/style.css")[0] == 200

                source = project / "app.py"
                source.write_text(source.read_text(encoding="utf-8").replace("Мукимов", "Reloaded"),
                                  encoding="utf-8")
                wait_for_page(process, port, "Reloaded")
            finally:
                stop(process)
    print("Installed wheel: scaffold, HTTP 303, assets and web reload verified.")


if __name__ == "__main__":
    main()
