<?php
declare(strict_types=1);

require __DIR__ . '/_layout.php';
siteStart('index');
?>
<main id="main">
    <section class="hero wrap" aria-labelledby="title">
        <div>
            <p class="eyebrow">ВЕРСИЯ <?= SITE_VERSION ?> · PYTHON 3.8+</p>
            <h1 id="title">Инструменты для Python</h1>
            <p class="intro">Создавай небольшие сайты, работай с паролями и настройками, оформляй вывод в терминале.</p>
            <div class="hero-actions">
                <a class="primary-link" href="web.php">Создать сайт <span aria-hidden="true">→</span></a>
                <?php pageLink('start'); ?>
            </div>
        </div>
        <div class="hero-example">
            <?php snippet('app.py', <<<'PY'
from mukimov.web import App

app = App()

@app.route("/")
def home():
    return "<h1>Привет!</h1>"

app.run()
PY); ?>
            <p class="example-address"><code>http://127.0.0.1:8000/</code></p>
        </div>
    </section>
    <section class="home-section wrap" aria-labelledby="paths">
        <p class="eyebrow">МАРШРУТЫ</p>
        <h2 id="paths">С чего начать</h2>
        <div class="path-grid">
            <?php foreach (['start' => '01', 'recipes' => '02', 'api' => '03'] as $id => $number): ?>
                <a class="path-card"<?= $id === 'start' ? ' id="install"' : '' ?> href="<?= h($id) ?>.php">
                    <span class="eyebrow"><?= h($number) ?></span>
                    <h3><?= h(SITE_PAGES[$id][0]) ?> <span aria-hidden="true">↗</span></h3>
                    <p><?= h(SITE_PAGES[$id][1]) ?></p>
                </a>
            <?php endforeach; ?>
        </div>
    </section>
    <section class="home-section wrap" aria-labelledby="modules">
        <p class="eyebrow">ПО ТЕМАМ</p>
        <h2 id="modules">Модули и команды</h2>
        <ul class="module-list">
            <?php foreach (['web' => 'mukimov.web', 'hashing' => 'mukimov.password', 'stars' => 'mukimov.stars()', 'colors' => 'mukimov.color', 'markdown' => 'mukimov.text.markdown', 'env' => 'mukimov.env', 'cli' => 'python -m mukimov'] as $id => $module): ?>
                <li id="<?= h($id === 'stars' ? 'password' : $id) ?>">
                    <a href="<?= h($id) ?>.php"><strong><?= h(SITE_PAGES[$id][0]) ?></strong><code><?= h($module) ?></code><span><?= h(SITE_PAGES[$id][1]) ?></span><span class="module-arrow" aria-hidden="true">→</span></a>
                </li>
            <?php endforeach; ?>
        </ul>
    </section>
    <section class="wrap release-strip" aria-labelledby="release">
        <div>
            <p class="eyebrow">ПОСЛЕДНИЕ ИЗМЕНЕНИЯ</p>
            <h2 id="release">Выпуск <?= SITE_VERSION ?></h2>
            <p>Команда <code>mukimov-startweb</code> создаёт сайт. После отправки формы можно <?php pageLink('web', 'перенаправить браузер на результат', 'form'); ?>.</p>
        </div>
        <?php pageLink('releases', 'Все выпуски →'); ?>
    </section>
</main>
<?php siteEnd(); ?>
