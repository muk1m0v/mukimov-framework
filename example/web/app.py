from pathlib import Path
from urllib.parse import urlencode

from mukimov import env
from mukimov.web import App, abort, redirect, render_template, request

app = App()


@app.route("/")
def home():
    return render_template("index.html", title="Мукимов")


@app.route("/about/")
def about():
    return render_template("about.html", title="О примере", assets=["CSS", "JavaScript", "SVG"])


@app.view(methods=["GET", "POST"])
@app.route("/hello")
def hello():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name or len(name) > 80:
            abort(400)
        return redirect("/hello?" + urlencode({"name": name}))
    name = request.query.get("name", "").strip()
    if name and len(name) <= 80:
        return render_template("home.html", title=f"Привет, {name}!")
    return render_template("home.html")


@app.errorhandler(400)
def bad_request():
    return render_template("errors/400.html", title="Запрос не принят")


@app.errorhandler(404)
def not_found():
    return render_template("errors/404.html", title="Страница не найдена")


if __name__ == "__main__":
    env.load(Path(__file__).with_name("settings.env"))
    app.run(port=env.integer("MUKIMOV_WEB_PORT", default=8017, min=1, max=65535))
