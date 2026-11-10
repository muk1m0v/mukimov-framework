<?php
declare(strict_types=1);

require __DIR__ . '/_layout.php';
docsStart('hashing', 'Модули', ['first-hash' => 'Создание и проверка', 'levels' => 'Уровни', 'storage' => 'Хранение', 'errors' => 'Возвращаемые значения']);
$levels = [
    'low' => ['600 000', '118', 'Самый быстрый'],
    'medium' => ['900 000', '121', 'По умолчанию'],
    'high' => ['1 200 000', '255', 'Самый затратный'],
];
?>
<section id="first-hash">
    <h2>Создание и проверка</h2>
    <p>Модуль <code>mukimov.password</code> входит в базовый пакет начиная с 0.2.2. Сохрани строку, полученную от <code>hash_password()</code>, и передай её вместе с введённым паролем в <code>verify_password()</code>.</p>
    <div class="example-options" id="hash-options" hidden>
        <label for="hash-level">Уровень в примере</label>
        <select id="hash-level">
            <?php foreach (array_keys($levels) as $name): ?>
                <option value="<?= h($name) ?>"><?= h($name) ?></option>
            <?php endforeach; ?>
        </select>
    </div>
    <div id="hash-example">
        <?php snippet('Python', <<<'PY'
from mukimov.password import hash_password, verify_password, low

password = '1234ok'
stored_hash = hash_password(password, level=low)

if verify_password('1234ok', stored_hash):
    print("Пароль подходит")
PY); ?>
    </div>
</section>
<section id="levels">
    <h2>Уровни</h2>
    <p>Уровень можно передать константой или строкой, например <code>level="high"</code>. Все уровни используют PBKDF2-HMAC-SHA256 с новой случайной солью при каждом вызове.</p>
    <div class="table-scroll" role="region" tabindex="0" aria-label="Уровни хеширования">
        <table>
            <thead><tr><th scope="col">Уровень</th><th scope="col">Итерации</th><th scope="col">Символов</th><th scope="col">Назначение</th></tr></thead>
            <tbody>
            <?php foreach ($levels as $name => [$iterations, $length, $description]): ?>
                <tr><th scope="row"><code><?= h($name) ?></code></th><td><?= h($iterations) ?></td><td><?= h($length) ?></td><td><?= h($description) ?></td></tr>
            <?php endforeach; ?>
            </tbody>
        </table>
    </div>
</section>
<section id="storage">
    <h2>Хранение</h2>
    <p>Храни запись целиком. Она содержит идентификатор формата, уровень, соль и производный ключ. Поле на 255 ASCII-символов вмещает все три уровня. Два вызова с одинаковым паролем обычно возвращают разные записи из-за случайной соли.</p>
    <p>Число итераций определяет вычислительную стоимость. В длину записи <code>high</code> также входят увеличенная соль и служебные поля.</p>
    <p><a href="https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html#pbkdf2">OWASP о хранении паролей и PBKDF2 ↗</a></p>
</section>
<section id="errors">
    <h2>Возвращаемые значения</h2>
    <p><code>verify_password()</code> возвращает <code>True</code> при совпадении и <code>False</code> при неверном пароле или повреждённой записи. Неверный тип аргумента вызывает <code>TypeError</code>, неизвестный уровень — <code>ValueError</code>.</p>
</section>
<?php docsEnd(['stars', 'recipes', 'api']); ?>
