<?php
declare(strict_types=1);

require __DIR__ . '/_layout.php';
docsStart('recipes', 'Первые шаги', ['login' => 'Проверка пароля', 'config' => 'Проверка конфигурации', 'report' => 'Цветной отчёт']);
?>
<section id="login">
    <h2>Проверить пароль в терминале</h2>
    <p>Первый ввод создаёт хеш, второй проверяет совпадение. В приложении первый шаг выполняют при регистрации, а при входе читают сохранённый хеш из базы.</p>
    <?php snippet('Python', <<<'PY'
from mukimov import stars
from mukimov.color import green, red
from mukimov.password import hash_password, verify_password

stored_hash = hash_password(stars("Задай пароль: "))
entered = stars("Повтори пароль: ")

if verify_password(entered, stored_hash):
    print(green("Пароль подходит"))
else:
    print(red("Пароль не совпадает"))
PY); ?>
    <p><?php pageLink('hashing', 'Подробнее о хранении хешей', 'storage'); ?></p>
</section>
<section id="config">
    <h2>Завершить запуск при ошибке в настройках</h2>
    <p>Сначала проверь наличие обязательных переменных, затем прочитай значения и проверь диапазон порта.</p>
    <?php snippet('Python', <<<'PY'
from mukimov import env

try:
    env.check(["API_URL", "APP_TOKEN"])
    port = env.integer("PORT", default=8080, min=1, max=65535)
except env.EnvError as error:
    raise SystemExit(str(error)) from None

print(f"Конфигурация принята. Порт: {port}")
PY); ?>
    <p><?php pageLink('env', 'Загрузить переменные из .env', 'load'); ?></p>
</section>
<section id="report">
    <h2>Собрать цветной отчёт</h2>
    <p>Пример использует <?php pageLink('markdown', 'Markdown-рендерер'); ?> из стандартной установки. Строку с ANSI-цветом можно передать в рендерер.</p>
    <?php snippet('Python', <<<'PY'
from mukimov.color import green
from mukimov.text import markdown

markdown.print("# Проверка\n\n- Статус: " + green("**Готово**"))
PY); ?>
</section>
<?php docsEnd(['start', 'api']); ?>
