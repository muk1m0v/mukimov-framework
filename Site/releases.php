<?php
declare(strict_types=1);

require __DIR__ . '/_layout.php';
docsStart('releases', 'Справка', ['v036' => '0.3.6', 'v035' => '0.3.5', 'v033' => '0.3.3', 'v032' => '0.3.2', 'v031' => '0.3.1', 'v030' => '0.3.0', 'v024' => '0.2.4', 'v023' => '0.2.3', 'v022' => '0.2.2', 'v021' => '0.2.1', 'v020' => '0.2.0', 'v018' => '0.1.8']);
?>
<section id="v036">
    <h2>0.3.6</h2>
    <p>Генератор создаёт пустую заготовку с <code>app.py</code> в корне и настройками в <code>core/conf.py</code>. Каталоги шаблонов задаются через <code>HTML_TEMPLATES</code> и <code>BASE_DIR</code>. Встроенная главная и подсказки на стандартных страницах ошибок доступны при <code>DEBUG = True</code>.</p>
</section>
<section id="v035">
    <h2>0.3.5</h2>
    <p>Исправлены ввод Unicode-паролей на Windows, откат при ошибке загрузки <code>.env</code> и блоки кода с отступом в Markdown.</p>
    <p><code>mukimov-startweb</code> создаёт новый сайт, а <code>redirect()</code> позволяет перенаправить браузер после отправки формы.</p>
</section>
<section id="v033">
    <h2>0.3.3</h2>
    <p>В шаблонах появились <?php pageLink('web', 'условия и циклы с разделителями {$ … $}', 'template-controls'); ?>. Сервер показывает версию <code>Mukimov Web Control</code> при запуске.</p>
</section>
<section id="v032">
    <h2>0.3.2</h2>
    <p>В <?php pageLink('web', 'примере формы', 'form'); ?> один обработчик принимает GET и POST через <code>app.view()</code> и <code>request.method</code>. При запуске сервер показывает сочетание клавиш для остановки.</p>
</section>
<section id="v031">
    <h2>0.3.1</h2>
    <p>Локальный сервер перезапускается при сохранении Python-файлов. В <?php pageLink('web', 'примере формы', 'form'); ?> адрес <code>/hello</code> можно открыть напрямую и отправить на него данные.</p>
</section>
<section id="v030">
    <h2>0.3.0</h2>
    <p>Добавлен <?php pageLink('web', 'mukimov.web'); ?> с маршрутами, HTML-шаблонами, статическими файлами и собственными страницами 400 и 404.</p>
    <p><code>app.run()</code> запускает локальный сервер. Порт по умолчанию — 8000.</p>
</section>
<section id="v024">
    <h2>0.2.4</h2>
    <p>Команда <?php pageLink('cli', 'mukimov example', 'example'); ?> запускает интерактивные примеры из установленного пакета.</p>
</section>
<section id="v023">
    <h2>0.2.3</h2>
    <p>Обычная установка <code>mukimov</code> автоматически подключает Markdown и загрузку <code>.env</code>. Команда <code>doctor</code> проверяет наличие этих зависимостей.</p>
</section>
<section id="v022">
    <h2>0.2.2</h2>
    <ul>
        <li>Модуль <?php pageLink('hashing', 'mukimov.password'); ?> создаёт хеши со случайной солью и проверяет пароли по сохранённым записям.</li>
        <li>Уровни <code>low</code>, <code>medium</code> и <code>high</code> отличаются числом итераций. Запись <code>high</code> занимает 255 символов.</li>
    </ul>
</section>
<section id="v021">
    <h2>0.2.1</h2>
    <ul>
        <li>Исправлена обработка клавиши Esc в Unix-терминалах. Ввод прекращается, если эхо нельзя отключить.</li>
        <li>Markdown и загрузка <code>.env</code> вынесены в дополнения.</li>
        <li>Справка работает офлайн, сравнение версий следует PEP 440, а wheel включает <code>py.typed</code>.</li>
    </ul>
</section>
<section id="v020">
    <h2>0.2.0</h2>
    <ul>
        <li>Добавлены <code>env.string()</code>, <code>env.list()</code>, <code>env.check()</code> и границы для <code>env.integer()</code>.</li>
        <li>Появились <code>mukimov doctor</code> и запуск команд через <code>python -m mukimov</code>.</li>
    </ul>
</section>
<section id="v018">
    <h2>0.1.8</h2>
    <p>Появились типизированные настройки окружения и явная загрузка <code>.env</code>.</p>
    <p><a href="<?= SITE_REPO ?>/blob/main/CHANGELOG.md">Полная история изменений на GitHub ↗</a></p>
</section>
<?php docsEnd(['hashing', 'cli', 'start']); ?>
