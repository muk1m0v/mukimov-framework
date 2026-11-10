<?php
declare(strict_types=1);

require __DIR__ . '/_layout.php';
docsStart('env', 'Модули', ['read' => 'Чтение настроек', 'load' => 'Загрузка .env', 'required' => 'Обязательные значения']);
?>
<section id="read">
    <h2>Чтение настроек</h2>
    <p>Функции читают окружение текущего процесса. Значение по умолчанию применяется, когда переменная отсутствует. Пустая строка или строка из пробелов вызывает <code>EnvError</code>.</p>
    <?php snippet('Python', <<<'PY'
from mukimov import env

debug = env.boolean("DEBUG", default=False)
port = env.integer("PORT", default=8080, min=1, max=65535)
hosts = env.list("HOSTS", default=["localhost"], separator=",")
PY); ?>
    <p><code>boolean()</code> понимает <code>true/false</code>, <code>yes/no</code>, <code>on/off</code> и <code>1/0</code>. <code>list()</code> удаляет пробелы вокруг элементов и пропускает пустые элементы.</p>
</section>
<section id="load">
    <h2>Загрузка .env</h2>
    <p>После <?php pageLink('start', 'обычной установки mukimov', 'install'); ?> вызови <code>env.load()</code>. Существующие значения окружения имеют приоритет. Передай <code>override=True</code>, если значения из файла должны их заменить.</p>
    <?php snippet('Файл .env', "API_URL=https://api.example.com\nDEBUG=false\nPORT=8080");
    snippet('Python', <<<'PY'
from mukimov import env

env.load(".env")
api_url = env.string("API_URL")
PY); ?>
</section>
<section id="required">
    <h2>Обязательные значения</h2>
    <p><code>env.required()</code> возвращает непустую строку как есть. <code>env.check()</code> перечисляет все отсутствующие и пустые обязательные переменные в одной ошибке. Значения настроек в сообщение не попадают.</p>
    <?php snippet('Python', <<<'PY'
from mukimov import env

env.check(["API_URL", "APP_TOKEN"])
token = env.required("APP_TOKEN")
PY); ?>
</section>
<?php docsEnd(['recipes', 'start', 'api']); ?>
