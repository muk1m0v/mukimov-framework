# Changelog

## 0.3.5

- Preserve Unicode characters in Windows password input by reading native console key events.
- Roll back environment changes if loading a `.env` file fails during a write.
- Render indented Markdown code blocks.
- Add `mukimov-startweb` and configurable aliases for CSS, JavaScript and image files.
- Add `redirect()` and `request.query` and use HTTP 303 after successful form submissions in the web example.
- Test the installed wheel and web reloading in CI and prepare tag-based PyPI Trusted Publishing.

## 0.3.3

- Add HTML template tags `{$ if … $}`, `{$ elif … $}`, `{$ else $}`, `{$ overif $}`, `{$ for … $}` and `{$ overfor $}` alongside standard Jinja syntax.
- Print the blue `Mukimov Web Control` version line on startup and demonstrate template tags in the example site.

## 0.3.2

- Add `app.view(methods=...)` and `request.method` for handlers shared by GET and POST.
- Update the web example with separate templates and port 8017.
- Print a blue stop shortcut after the green startup address, with a macOS label.

## 0.3.1

- Reload the local web server after saving Python files.
- Make the example form accessible by GET and handle submissions by POST at `/hello`.

## 0.3.0

- Add `mukimov.web` with GET and POST routes, Jinja templates, static files and custom error pages.
- Add a local server on `127.0.0.1:8000` with a configurable port and an example website in the source archive.

## 0.2.4

- Add `mukimov example` and `python -m mukimov example` to run the interactive demo from an installed package.

## 0.2.3

- Install Markdown rendering and dotenv loading dependencies with the standard package installation.
- Report missing dependencies in `mukimov doctor` and verify both features after a single wheel install in CI.

## 0.2.2

- Added `mukimov.password.hash_password()` and `verify_password()` with salted PBKDF2-HMAC-SHA256.
- Added `low`, `medium` and `high` presets. The `high` preset produces a 255-character record.
- Updated the README and PHP documentation site with password storage examples.

## 0.2.1

- Stop password input if the terminal cannot disable echo.
- Handle Unix escape sequences without blocking on a lone Esc, and restore terminal settings after input.
- Move Markdown rendering and dotenv loading into the `markdown` and `env` extras.
- Keep CLI help offline and compare update versions using PEP 440.
- Include the `py.typed` marker and check built wheels in CI.

## 0.2.0

- Added `env.string()` and `env.list()` with typed defaults.
- Added inclusive `min` / `max` bounds to `env.integer()`.
- Added `env.check()` to report all missing or empty settings together.
- Added offline `mukimov doctor` diagnostics.
- Added `python -m mukimov` for all CLI commands.
- Kept environment values out of configuration errors and diagnostics.
- Updated examples and added tests for the new public APIs.

## 0.1.8

- Added typed environment settings and explicit `.env` loading.
