<?php
declare(strict_types=1);

require __DIR__ . '/_layout.php';
docsStart('markdown', 'Модули', ['setup' => 'Установка', 'report' => 'Отчёт с таблицей', 'render' => 'Получение строки', 'syntax' => 'Поддерживаемый синтаксис']);
?>
<section id="setup">
    <h2>Установка</h2>
    <p>С версии 0.2.3 Markdown доступен после <?php pageLink('start', 'обычной установки mukimov', 'install'); ?>.</p>
</section>
<section id="report">
    <h2>Отчёт с таблицей</h2>
    <p><code>markdown.print()</code> форматирует текст и сразу выводит его в терминал.</p>
    <?php snippet('Python', <<<'PY'
from mukimov.text import markdown

markdown.print("""# Проверка сервисов

| Сервис | Статус |
| --- | --- |
| API | **Готов** |
| База | *Ожидает* |
""")
PY); ?>
</section>
<section id="render">
    <h2>Получение строки</h2>
    <p><code>markdown.render()</code> возвращает оформленный текст с ANSI-кодами. Уже существующие ANSI-стили сохраняются, поэтому передавай рендереру текст из доверенного источника.</p>
    <?php snippet('Python', <<<'PY'
from mukimov.text import markdown

report = markdown.render("**Готово** · `200 OK`")
print(report)
PY); ?>
</section>
<section id="syntax">
    <h2>Поддерживаемый синтаксис</h2>
    <ul>
        <li>Заголовки, выделение текста, списки и цитаты.</li>
        <li>Таблицы, горизонтальные линии и ссылки с URL рядом с текстом.</li>
        <li>Встроенный код и блоки, ограждённые тройными обратными кавычками.</li>
    </ul>
</section>
<?php docsEnd(['colors', 'recipes', 'api']); ?>
