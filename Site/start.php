<?php
declare(strict_types=1);

require __DIR__ . '/_layout.php';
docsStart('start', 'Первые шаги', ['install' => 'Установка', 'first-script' => 'Первая программа']);
?>
<section id="install">
    <h2>1. Установи пакет</h2>
    <p>Нужен Python 3.8 или новее. Создай виртуальное окружение в папке своего проекта и запускай pip через его интерпретатор.</p>
    <?php snippet('Windows · PowerShell', <<<'SH'
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install mukimov
.\.venv\Scripts\python.exe -m mukimov --version
SH);
    snippet('Ubuntu · Shell', <<<'SH'
python3 -m venv .venv
.venv/bin/python -m pip install mukimov
.venv/bin/python -m mukimov --version
SH); ?>
    <p>С версии 0.2.3 эта команда устанавливает всё необходимое для хеширования, цветов, Markdown и загрузки <code>.env</code>. Если у тебя есть wheel, подставь путь к файлу вместо имени <code>mukimov</code> в команде установки.</p>
</section>
<section id="first-script">
    <h2>2. Запусти первую программу</h2>
    <p>Сохрани пример как <code>check.py</code>. Он читает порт из окружения и показывает его зелёным. При отсутствии <code>PORT</code> используется 8080.</p>
    <?php snippet('Python · check.py', <<<'PY'
from mukimov import env
from mukimov.color import green

port = env.integer("PORT", default=8080, min=1, max=65535)
print(green(f"Порт: {port}"))
PY);
    snippet('Windows · PowerShell', '.\.venv\Scripts\python.exe check.py');
    snippet('Ubuntu · Shell', '.venv/bin/python check.py'); ?>
</section>
<?php docsEnd(['recipes', 'env', 'cli']); ?>
