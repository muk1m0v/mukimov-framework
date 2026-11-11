# Корень проекта: папка с app.py, независимо от папки запуска терминала.
# Пример пути к файлу: BASE_DIR / "content" / "css" / "style.css"
from mukimov.dirs import BASE_DIR

# В Python логические значения пишутся True и False.
# True: встроенная главная для пустого index.html и подсказки на страницах ошибок.
# Пример отключения: DEBUG = False
DEBUG = True

# Показывать цветные строки HTTP-запросов в терминале.
# Пример: SHOW_SERVER_STATUS_IN_TERMINAL = False скрывает строки GET/POST и статусы.
# Сообщения запуска и ошибки приложения остаются видны.
SHOW_SERVER_STATUS_IN_TERMINAL = True

# Каталоги HTML-шаблонов проверяются по порядку.
# Пример: HTML_TEMPLATES = [BASE_DIR / "pages", BASE_DIR / "templates"]
# В app.py: return render_template("index.html", title="Мой сайт")
HTML_TEMPLATES = [BASE_DIR / "templates"]

# True: разрешены короткие имена ресурсов в HTML, объявленные ниже.
# False: используй прямые адреса, например href="/content/css/style.css".
# Пример короткого имени: href="{$ 'main_style' $}"
ALL_CONTENT_STATIC = True

# CSS-файлы. Путь задаёт адрес в браузере и папку внутри корня проекта.
# Пример другого пути: "STYLE_MAIN_PATH": "/assets/css/"
CSS_SETTING = {
    "STYLE_MAIN_PATH": "/content/css/",
    # Создай content/css/style.css, затем раскомментируй следующую строку.
    # "style.css": "main_style",
}
# HTML: <link rel="stylesheet" href="{$ 'main_style' $}">

# JavaScript-файлы. В этой папке разрешены файлы .js и .mjs.
# Пример другого пути: "SCRIPT_MAIN_PATH": "/assets/js/"
JAVASCRIPT_SETTING = {
    "SCRIPT_MAIN_PATH": "/content/js/",
    # Создай content/js/script.js, затем раскомментируй следующую строку.
    # "script.js": "my_script",
}
# HTML: <script src="{$ 'my_script' $}" defer></script>

# Изображения. Например, PNG, JPEG, SVG или WebP.
# Пример другого пути: "IMAGE_MAIN_PATH": "/assets/img/"
IMAGE_SETTING = {
    "IMAGE_MAIN_PATH": "/content/img/",
    # Создай content/img/logo.png, затем раскомментируй следующую строку.
    # "logo.png": "logo",
}
# HTML: <img src="{$ 'logo' $}" alt="Логотип">
