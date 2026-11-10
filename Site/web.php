<?php
declare(strict_types=1);

require __DIR__ . '/_layout.php';
docsStart('web', 'Модули', ['setup' => 'Первый сайт', 'static' => 'CSS, JS и картинки', 'form' => 'Форма', 'template-controls' => 'Условия и циклы', 'errors' => 'Ошибки 400 и 404']);
?>
<section id="setup">
    <h2>Первый сайт</h2>
    <p>В корне проекта запусти <code>python -m mukimov startweb</code>, затем <code>python app.py</code>. Генератор создаёт <code>app.py</code> в текущей папке, настройки в <code>core/conf.py</code> и пустой <code>templates/index.html</code>, если своего шаблона ещё нет.</p>
    <?php snippet('Python · core/conf.py', <<<'PY'
from mukimov.dirs import BASE_DIR

DEBUG = True
HTML_TEMPLATES = [BASE_DIR / "templates"]
PY); ?>
    <p>Пока главная пустая, <code>DEBUG = True</code> показывает встроенную стартовую страницу. Стандартные страницы ошибок тоже сообщают о включённом режиме. Чтобы убрать эти подсказки, укажи <code>DEBUG = False</code>.</p>
    <?php snippet('Терминал', 'python -m pip install --upgrade mukimov');
    snippet('Python · app.py', <<<'PY'
from mukimov.web import App, render_template

app = App()

@app.route("/")
def home():
    return render_template("index.html", title="Мой сайт")

if __name__ == "__main__":
    app.run(port=8017)
PY);
    snippet('HTML · templates/index.html', <<<'HTML'
<!doctype html>
<html lang="ru">
<meta charset="utf-8">
<title>{{ title }}</title>
<h1>{{ title }}</h1>
HTML);
    snippet('Терминал', 'python app.py'); ?>
    <p>Открой <code>http://127.0.0.1:8017/</code>. Без аргумента <code>port</code> сервер использует порт 8000. При сохранении Python-файлов сервер перезапускается. После сохранения обнови страницу в браузере. Отключить перезапуск можно через <code>app.run(reload=False)</code>.</p>
    <?php snippet('Вывод при запуске', <<<'TEXT'
Сервер запущен: http://127.0.0.1:8017
Чтобы остановить сервер, используйте комбинацию: Ctrl + C
Mukimov Web Control - v0.3.7
TEXT); ?>
</section>
<section id="static">
    <h2>CSS, JavaScript и картинки</h2>
    <p>В сгенерированном проекте для ресурсов есть пустые папки <code>content/css/</code>, <code>content/js/</code> и <code>content/img/</code>. Добавь свои файлы и подключи их по адресам <code>/content/css/...</code>, <code>/content/js/...</code> и <code>/content/img/...</code>. Папка <code>static/</code> по-прежнему работает для приложений, которые используют адреса <code>/static/</code>.</p>
    <?php snippet('HTML', <<<'HTML'
<link rel="stylesheet" href="/static/css/style.css">
<script src="/static/js/app.js" defer></script>
<img src="/static/img/logo.svg" alt="Логотип">
HTML); ?>
</section>
<section id="form">
    <h2>Форма</h2>
    <p>Открытие <code>/hello</code> в браузере отправляет GET и показывает форму. Успешный POST получает 303, после чего браузер открывает результат через GET. При обновлении страницы форма повторно не отправляется.</p>
    <?php snippet('Python · app.py', <<<'PY'
from urllib.parse import urlencode
from mukimov.web import abort, redirect, request

@app.view(methods=["GET", "POST"])
@app.route("/hello")
def hello():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            abort(400)
        return redirect("/hello?" + urlencode({"name": name}))
    name = request.query.get("name", "").strip()
    if name:
        return render_template("home.html", title=f"Привет, {name}!")
    return render_template("home.html")
PY);
    snippet('HTML · templates/home.html', <<<'HTML'
<h1>Приветствие</h1>
<form method="post" action="/hello">
    <label for="name">Имя</label>
    <input id="name" name="name">
    <button>Поздороваться</button>
    {$ if title $}
        <h2>{{ title }}</h2>
    {$ overif $}
</form>
HTML); ?>
</section>
<section id="template-controls">
    <h2>Условия и циклы</h2>
    <p>С версии 0.3.3 в <code>mukimov.web</code> можно писать условия и циклы с разделителями <code>{$ … $}</code>. Передай <code>title</code> и список <code>items</code> через <code>render_template()</code>.</p>
    <?php snippet('HTML', <<<'HTML'
{$ if title $}
    <h1>{{ title }}</h1>
{$ overif $}

<ul>
    {$ for item in items $}
        <li>{{ item }}</li>
    {$ overfor $}
</ul>
HTML); ?>
    <p>Для альтернативной ветки используй <code>{$ else $}</code>. Обычные теги Jinja <code>{% … %}</code> можно использовать в том же шаблоне.</p>
</section>
<section id="errors">
    <h2>Ошибки 400 и 404</h2>
    <p>Пустая форма из примера возвращает 400. Неизвестный адрес возвращает 404. Чтобы заменить стандартную страницу, добавь обработчик. HTTP-статус останется тем же.</p>
    <?php snippet('Python · app.py', <<<'PY'
@app.errorhandler(400)
def bad_request():
    return "<h1>Заполни форму</h1>"

@app.errorhandler(404)
def not_found():
    return '<h1>Страница не найдена</h1><a href="/">На главную</a>'
PY); ?>
</section>
<?php docsEnd(['start', 'api', 'releases']); ?>
