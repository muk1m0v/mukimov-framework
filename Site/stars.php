<?php
declare(strict_types=1);

require __DIR__ . '/_layout.php';
docsStart('stars', 'Модули', ['example' => 'Пример ввода', 'keys' => 'Клавиши', 'redirect' => 'Перенаправленный ввод']);
?>
<section id="example">
    <h2>Пример ввода</h2>
    <p><code>stars(prompt="Password: ", mask="*")</code> возвращает введённый пароль как строку. При наборе символы пароля заменяются маской. Для корректного стирания выбирай маску шириной в одну колонку, например <code>*</code> или <code>•</code>.</p>
    <?php snippet('Python', <<<'PY'
from mukimov import stars
from mukimov.color import cyan

password = stars(cyan("Пароль: "), mask="•")
PY); ?>
    <p class="note">Маска показывает длину ввода. Для записи в базу используй <?php pageLink('hashing', 'хеширование пароля'); ?>.</p>
</section>
<section id="keys">
    <h2>Клавиши</h2>
    <ul>
        <li><kbd>Enter</kbd> завершает ввод и возвращает строку.</li>
        <li><kbd>Backspace</kbd> стирает последний символ и его маску.</li>
        <li><kbd>Ctrl+C</kbd> прерывает ввод через <code>KeyboardInterrupt</code>.</li>
        <li><kbd>Ctrl+D</kbd> при пустом вводе вызывает <code>EOFError</code>.</li>
    </ul>
</section>
<section id="redirect">
    <h2>Перенаправленный ввод</h2>
    <p>Если стандартный ввод перенаправлен, <code>stars()</code> пробует получить пароль скрыто через <code>getpass</code>. Если отключить эхо невозможно, возникает <code>RuntimeError</code>.</p>
    <p>Для интерактивного ввода запускай скрипт в обычном терминале Windows, Ubuntu или macOS.</p>
</section>
<?php docsEnd(['hashing', 'colors', 'recipes']); ?>
