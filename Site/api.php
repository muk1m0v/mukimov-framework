<?php
declare(strict_types=1);

require __DIR__ . '/_layout.php';
$sections = [
    'web' => 'Веб',
    'password' => 'Пароли',
    'display' => 'Вывод',
    'settings' => 'Окружение',
    'commands' => 'CLI',
];
$reference = [
    'web' => [
        ['App(*, root=None)', 'Создаёт приложение и находит templates/ и static/.', 'web', 'setup'],
        ['app.route(path, *, methods=None)', 'Связывает адрес с функцией Python. По умолчанию принимает GET.', 'web', 'setup'],
        ['app.view(*, methods)', 'Задаёт методы для маршрутов обработчика, где methods не указан.', 'web', 'form'],
        ['request.method', 'Возвращает метод обработчика. Запрос HEAD использует обработчик GET.', 'web', 'form'],
        ['render_template(template_name, /, **context) → str', 'Подставляет данные в HTML-шаблон.', 'web', 'setup'],
        ['request.form', 'Даёт доступ к полям HTML-формы.', 'web', 'form'],
        ['request.query', 'Возвращает параметры адреса.', 'web', 'form'],
        ['redirect(location)', 'Перенаправляет на локальный адрес с HTTP 303.', 'web', 'form'],
        ['abort(status)', 'Прерывает запрос с указанной HTTP-ошибкой.', 'web', 'errors'],
        ['app.errorhandler(status)', 'Назначает шаблон страницы ошибки через функцию.', 'web', 'errors'],
        ['app.run(*, port=8000, reload=True)', 'Запускает локальный сервер и перезапускает его при изменении Python-файлов.', 'web', 'setup'],
    ],
    'password' => [
        ['stars(prompt="Password: ", mask="*") → str', 'Читает пароль в терминале с маской.', 'stars', 'example'],
        ['hash_password(password, level="medium") → str', 'Создаёт запись с солью для хранения пароля.', 'hashing', 'levels'],
        ['verify_password(password, stored_hash) → bool', 'Проверяет пароль по сохранённой записи.', 'hashing', 'errors'],
    ],
    'display' => [
        ['color.red(text) → str', 'Возвращает строку в выбранном цвете. В палитре 12 функций.', 'colors', 'palette'],
        ['markdown.render(text) → str', 'Возвращает оформленный Markdown.', 'markdown', 'render'],
        ['markdown.print(text) → None', 'Печатает оформленный Markdown.', 'markdown', 'report'],
    ],
    'settings' => [
        ['env.load(path=".env", *, override=False) → tuple', 'Загружает настройки и возвращает имена из файла.', 'env', 'load'],
        ['env.check(names) → None', 'Проверяет наличие всех обязательных переменных.', 'env', 'required'],
        ['env.required(name) → str', 'Возвращает обязательное непустое значение.', 'env', 'required'],
        ['env.string(name, default=…) → str', 'Возвращает строку с необязательным значением по умолчанию.', 'env', 'load'],
        ['env.boolean(name, default=…) → bool', 'Преобразует переменную в логическое значение.', 'env', 'read'],
        ['env.integer(name, default=…, *, min=None, max=None) → int', 'Читает целое число и проверяет границы включительно.', 'env', 'read'],
        ['env.list(name, default=…, *, separator=",") → list[str]', 'Делит значение на строки по разделителю.', 'env', 'read'],
        ['env.EnvError', 'Ошибка отсутствующей или недопустимой настройки.', 'env', 'required'],
    ],
    'commands' => [
        ['python -m mukimov --help', 'Показывает команды и параметры.', 'cli', 'commands'],
        ['python -m mukimov --version', 'Показывает версию пакета.', 'cli', 'commands'],
        ['python -m mukimov example', 'Открывает интерактивное меню примеров.', 'cli', 'example'],
        ['python -m mukimov doctor', 'Диагностирует установку офлайн.', 'cli', 'doctor'],
        ['python -m mukimov update', 'Проверяет PyPI и при необходимости запускает pip.', 'cli', 'update'],
    ],
];
docsStart('api', 'Справка', $sections);
?>
<div class="api-search" id="api-search" hidden>
    <label for="api-filter">Найти функцию или команду</label>
    <input type="search" id="api-filter" placeholder="Например, hash_password">
    <p id="api-status" role="status"></p>
</div>
<p>Многоточие в сигнатуре означает необязательный параметр. Без <code>default</code> функция чтения требует, чтобы переменная существовала.</p>
<?php foreach ($reference as $section => $rows): ?>
    <section id="<?= h($section) ?>">
        <h2><?= h($sections[$section]) ?></h2>
        <dl class="api-list">
            <?php foreach ($rows as [$signature, $description, $page, $anchor]): ?>
                <div data-api-entry>
                    <dt><code><?= h($signature) ?></code></dt>
                    <dd><?= h($description) ?> <?php pageLink($page, 'Пример →', $anchor); ?></dd>
                </div>
            <?php endforeach; ?>
        </dl>
    </section>
<?php endforeach; ?>
<?php docsEnd(['start', 'recipes', 'releases']); ?>
