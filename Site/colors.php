<?php
declare(strict_types=1);

require __DIR__ . '/_layout.php';
docsStart('colors', 'Модули', ['messages' => 'Сообщения', 'palette' => 'Палитра', 'ansi' => 'Как работает вывод']);
?>
<section id="messages">
    <h2>Сообщения</h2>
    <p>Цветовые функции возвращают строку. Её можно вывести через <code>print()</code> или использовать как приглашение для <code>input()</code> и <code>stars()</code>.</p>
    <?php snippet('Python', <<<'PY'
from mukimov.color import green, red

print(green("Подключено"))
print(red("Ошибка подключения"))
PY); ?>
</section>
<section id="palette">
    <h2>Палитра</h2>
    <p>Все функции доступны в <code>mukimov.color</code> и принимают один аргумент <code>text: str</code>.</p>
    <div class="palette" aria-label="Названия цветов">
        <?php foreach (['red', 'green', 'blue', 'yellow', 'orange', 'purple', 'pink', 'cyan', 'lime', 'gray', 'white', 'gold'] as $color): ?>
            <span class="swatch"><?= h($color) ?></span>
        <?php endforeach; ?>
    </div>
</section>
<section id="ansi">
    <h2>Как работает вывод</h2>
    <p>В начале строки добавляется ANSI-код цвета, в конце — код сброса. Цвет зависит от палитры терминала. При перенаправлении вывода управляющие коды сохраняются в строке, поэтому в обычный текстовый файл передавай исходное сообщение.</p>
    <p>Функции ожидают непустой текст. Передача числа вызывает <code>TypeError</code>, а пустой строки или строки из пробелов — <code>ValueError</code>.</p>
</section>
<?php docsEnd(['markdown', 'stars', 'api']); ?>
