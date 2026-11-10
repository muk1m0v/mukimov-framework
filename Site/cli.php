<?php
declare(strict_types=1);

require __DIR__ . '/_layout.php';
docsStart('cli', 'Модули', ['commands' => 'Список команд', 'example' => 'Демонстрация', 'doctor' => 'Диагностика', 'update' => 'Обновление']);
?>
<section id="commands">
    <h2>Список команд</h2>
    <p>Выполняй команды через тот же Python, в который установил пакет.</p>
    <?php snippet('Терминал', "python -m mukimov --help\npython -m mukimov --version\npython -m mukimov example\npython -m mukimov doctor\npython -m mukimov update"); ?>
    <p>Если исполняемый файл доступен в <code>PATH</code>, можно писать <code>mukimov</code> вместо <code>python -m mukimov</code>.</p>
</section>
<section id="example">
    <h2>Демонстрация</h2>
    <p>Начиная с 0.2.4 команда <code>mukimov example</code> открывает меню примеров из любой папки. Нажми 1 для проверки маски пароля, 2 для хеширования или 0 для выхода.</p>
    <?php snippet('Терминал', 'python -m mukimov example'); ?>
</section>
<section id="doctor">
    <h2>Диагностика</h2>
    <p><code>doctor</code> показывает версию Python, путь к интерпретатору и пакету, наличие команды в <code>PATH</code> и доступность зависимостей. Команда работает офлайн. Если <code>mukimov</code> не находится, запусти модуль напрямую.</p>
    <?php snippet('Терминал', "python -m pip show mukimov\npython -m mukimov doctor"); ?>
</section>
<section id="update">
    <h2>Обновление</h2>
    <p><code>update</code> проверяет версию на PyPI и при необходимости запускает pip через текущий интерпретатор. Обновление также можно выполнить непосредственно через pip.</p>
    <?php snippet('Терминал', 'python -m pip install --upgrade mukimov'); ?>
</section>
<?php docsEnd(['start', 'releases']); ?>
