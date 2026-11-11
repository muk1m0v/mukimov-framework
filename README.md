# mukimov

[**mukimov на PyPI**](https://pypi.org/project/mukimov/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://pypi.org/project/mukimov/)
[![MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)

Инструменты для Python. Создавай небольшие сайты, хешируй пароли для хранения, оформляй вывод в терминале и читай настройки из окружения.

## Документация

На сайте есть быстрый старт для Windows и Ubuntu, примеры для каждого модуля, готовые рецепты и справочник функций. [Подробная документация](https://mukimov.click/)

## Установка

Обычная установка включает веб-модуль, Markdown и загрузку `.env`. pip устанавливает нужные зависимости автоматически.

```console
python -m pip install mukimov
```

Если пакет уже установлен, обнови его и проверь версию.

```console
python -m pip install --upgrade mukimov
python -m mukimov --version
```

## Сайт на Python и HTML

### Готовый проект с CSS, JavaScript и картинкой

Из папки, где нужен проект, запусти:

```console
python -m mukimov startweb
python app.py
```

Без имени генератор использует текущую папку. Запускай его из корня проекта. Чтобы создать новый каталог, можно явно передать имя, например `python -m mukimov startweb my_site`. Сайт запускается на [127.0.0.1:8000](http://127.0.0.1:8000/).

В новом шаблоне проекта `app.py` лежит в корне, настройки находятся в `core/conf.py`, а `templates/index.html` и папки `content/css`, `content/js` и `content/img` изначально пустые.

```python
from mukimov.dirs import BASE_DIR

DEBUG = True
SHOW_SERVER_STATUS_IN_TERMINAL = True
HTML_TEMPLATES = [BASE_DIR / "templates"]
```

Пока главная пустая, `DEBUG = True` показывает встроенную стартовую страницу. Стандартные страницы ошибок тоже объясняют, почему включён этот режим. Когда добавишь свой HTML, главная покажет его. С `DEBUG = False` встроенная стартовая страница и подсказки об ошибках отключаются.

Параметр `SHOW_SERVER_STATUS_IN_TERMINAL` по умолчанию равен `True`. Значение `False` отключает строки HTTP-запросов в терминале. Сообщения запуска и ошибки приложения остаются видны. В `core/conf.py` каждого нового проекта есть комментарии с примерами настройки шаблонов, CSS, JavaScript и изображений. Значения Python пишутся `True` и `False`.

В `core/conf.py` параметр `ALL_CONTENT_STATIC = True` включает короткие имена. Добавь свои файлы в соответствующие папки и укажи их имена в настройках. Например, `"style.css": "main_style"` в `CSS_SETTING` позволяет написать:

```html
<link rel="stylesheet" href="{$ 'main_style' $}">
<script src="{$ 'my_script' $}" defer></script>
<img src="{$ 'example_photo' $}" alt="">
```

При `ALL_CONTENT_STATIC = False` указывай прямой адрес, например `href="/content/css/style.css"`. Ключи `"STYLE_MAIN_PATH"`, `"SCRIPT_MAIN_PATH"` и `"IMAGE_MAIN_PATH"` задают URL и соответствующие папки внутри проекта. Например, `"STYLE_MAIN_PATH": "/assets/css/"` указывает на папку `assets/css/` рядом с `app.py`.

### Запуск вручную

Сохрани как `app.py`.

```python
from mukimov.web import App, render_template

app = App()

@app.route("/")
def home():
    return render_template("index.html", title="Мой сайт")

if __name__ == "__main__":
    app.run(port=8000)
```

Создай рядом файл `templates/index.html` с содержимым `<h1>{{ title }}</h1>`. Запусти `python app.py` и открой [локальный сайт](http://127.0.0.1:8000/). После сохранения Python-файла сервер перезапустится. Обнови страницу, чтобы увидеть изменения. Отключить перезапуск можно через `app.run(reload=False)`.

CSS, JavaScript и картинки из папки `static/` доступны по адресам `/static/...`. Добавь `@app.view(methods=["GET", "POST"])` над `@app.route("/hello")`, чтобы один обработчик открывал и принимал форму. Метод запроса доступен через `request.method`, поля формы — через `request.form`. Страницы 400 и 404 можно оформить через `app.errorhandler()`. Встроенный сервер предназначен для локальной разработки. [Документация веб-модуля](https://mukimov.click/web.php)

После успешной отправки формы верни `redirect("/result")` из обработчика. Сервер ответит кодом 303, и браузер откроет страницу результата через GET. Параметры её адреса доступны через `request.query`.

В HTML-шаблонах можно использовать условия и циклы. Передай `title` и `items` через `render_template()`.

```html
{$ if title $}
    <h1>{{ title }}</h1>
{$ overif $}

<ul>
    {$ for item in items $}
        <li>{{ item }}</li>
    {$ overfor $}
</ul>
```

## Хеширование пароля

Модуль `mukimov.password` создаёт хеш для хранения и проверяет пароль по сохранённому хешу.

```python
from mukimov.password import hash_password, low, verify_password

password = '1234ok'
stored_hash = hash_password(password, level=low)

if verify_password('1234ok', stored_hash):
    print('Пароль подходит')
```

Уровень можно передать как строку (`level="high"`) или импортировать как константу (`level=high`).

| Уровень | Итерации PBKDF2-HMAC-SHA256 | Длина записи |
| --- | ---: | ---: |
| `low` · самый быстрый | 600 000 | 118 |
| `medium` · по умолчанию | 900 000 | 121 |
| `high` · самый затратный | 1 200 000 | 255 |

Каждый вызов создаёт новую случайную соль, поэтому повторное хеширование того же пароля даёт другую строку. Сохраняй всю строку, включая версию формата, уровень и соль. При входе передавай введённый пароль и сохранённую строку в `verify_password()`. Функция возвращает `False` при неверном пароле или повреждённой записи.

В `high` ровно 255 ASCII-символов с учётом служебных полей и увеличенной соли. Разницу в вычислительной стоимости задаёт число итераций. Все три уровня используют один алгоритм. Порог для `low` взят из рекомендаций по PBKDF2. [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html#pbkdf2)

## Ввод пароля

```python
from mukimov import stars
from mukimov.color import cyan

password = stars(cyan("Пароль: "), mask="•")
```

```text
Пароль: ••••••
```

`stars(prompt="Password: ", mask="*")` возвращает введённый пароль как обычную строку Python. Не печатай её и не записывай в логи. Маска показывает длину ввода. Для корректного стирания маски через Backspace выбирай символ шириной в одну колонку, например `*`, `#` или `•`.

Ввод с маской работает в терминалах Windows, Linux и macOS. Enter завершает ввод, Backspace удаляет последний символ, Ctrl+C прерывает ввод, а Ctrl+D на пустом вводе вызывает `EOFError`. Если стандартный ввод перенаправлен, библиотека пробует скрытый ввод через `getpass`. Если отключить эхо невозможно, она прекращает ввод с `RuntimeError`.

## Цвет и Markdown

```python
from mukimov.color import green, red

print(green("Готово"))
print(red("Ошибка"))
```

Функции цвета возвращают строки с ANSI-кодами. Доступны `red`, `green`, `blue`, `yellow`, `orange`, `purple`, `pink`, `cyan`, `lime`, `gray`, `white` и `gold`.

Модуль `markdown` выводит заголовки, списки, таблицы, ссылки и блоки кода в терминал.

```python
from mukimov.text import markdown

markdown.print("# Отчёт\n\n- **Статус:** готово")
text = markdown.render("**Готово**")  # Возвращает оформленную строку
```

## Настройки окружения

```python
from mukimov import env

env.load(".env")
env.check(["APP_TOKEN", "API_URL"])

token = env.required("APP_TOKEN")
api_url = env.string("API_URL")
debug = env.boolean("DEBUG", default=False)
port = env.integer("PORT", default=8080, min=1, max=65535)
hosts = env.list("HOSTS", default=["localhost"], separator=",")
```

`env.load()` вызывается явно. По умолчанию существующие переменные окружения имеют приоритет. Чтобы заменить их значениями из файла, передай `override=True`. Методы чтения работают и без файла `.env`.

Значения по умолчанию применяются к отсутствующим переменным. Пустое значение в окружении считается ошибкой. `env.check()` сообщает обо всех отсутствующих и пустых обязательных переменных сразу. Сообщения `EnvError` указывают имена настроек без их значений.

## Команды

```console
python -m mukimov --help
python -m mukimov --version
python -m mukimov doctor
python -m mukimov example
python -m mukimov update
```

Те же команды доступны через `mukimov`, если он есть в `PATH`. Справка, версия и `doctor` работают офлайн. `doctor` показывает используемый Python и доступность компонентов. `update` проверяет PyPI и при необходимости запускает обновление через pip для текущего интерпретатора.

`mukimov example` открывает интерактивное меню. Нажми `1` для проверки маски пароля, `2` для хеширования или `0` для выхода. В меню также есть цвета, Markdown, настройки окружения и диагностика.

## Разработка

В исходном проекте можно попробовать `mukimov.web` для локального сайта на Python и HTML. В примере есть маршруты, HTML-форма, CSS, JavaScript, SVG и страницы ошибок 400 и 404. [Запуск примера](example/web/README.md)

```console
python -m pip install -e .
python -m pip install build twine
python -B -m unittest discover -s tests -q
python -m build
python -m twine check --strict dist/*
```

Релиз запускается тегом `v<версия>`. В PyPI Trusted Publishing для проекта укажи владельца `muk1m0v`, репозиторий `mukimov-framework`, файл `publish.yml` и окружение `pypi`. Workflow публикует проверенные wheel и архив исходников с подтверждением происхождения. [Настройка Trusted Publishing](https://docs.pypi.org/trusted-publishers/adding-a-publisher/)

[История изменений](CHANGELOG.md) · [Лицензия MIT](LICENSE)
