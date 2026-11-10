<?php
declare(strict_types=1);

const SITE_VERSION = '0.3.6';
const SITE_REPO = 'https://github.com/muk1m0v/mukimov-framework';
const SITE_PYPI = 'https://pypi.org/project/mukimov/';
const SITE_PAGES = [
    'index' => ['Обзор', 'Возможности mukimov и путеводитель по сайту.'],
    'start' => ['Быстрый старт', 'Установка на Windows и Ubuntu и первая программа.'],
    'recipes' => ['Рецепты', 'Готовые сценарии для паролей, конфигурации и терминального вывода.'],
    'web' => ['Сайты на Python', 'Маршруты, HTML-шаблоны, статические файлы и страницы ошибок.'],
    'hashing' => ['Хеширование паролей', 'Хранение и проверка паролей с помощью mukimov.password.'],
    'stars' => ['Ввод пароля', 'Маскировка ввода в терминале с помощью stars().'],
    'colors' => ['Цвета', 'Оформление сообщений и приглашений с помощью ANSI-цветов.'],
    'markdown' => ['Markdown', 'Таблицы, списки и форматирование Markdown в терминале.'],
    'env' => ['Настройки окружения', 'Загрузка .env и чтение типизированных настроек.'],
    'cli' => ['Команды CLI', 'Версия, диагностика установки и обновление пакета.'],
    'api' => ['Справочник API', 'Указатель функций и сигнатур mukimov.'],
    'releases' => ['История версий', 'Изменения в выпусках mukimov.'],
];
const SITE_NAV = [
    'Первые шаги' => ['index', 'start', 'recipes'],
    'Модули' => ['web', 'hashing', 'stars', 'colors', 'markdown', 'env', 'cli'],
    'Справка' => ['api', 'releases'],
];

function h(string $text): string
{
    return htmlspecialchars($text, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

function pageLink(string $id, ?string $label = null, string $anchor = ''): void
{
    $href = $id . '.php' . ($anchor === '' ? '' : '#' . $anchor);
    echo '<a href="' . h($href) . '">' . h($label ?? SITE_PAGES[$id][0]) . '</a>';
}

function copyButton(string $label = 'Копировать код'): void
{
    ?>
    <button type="button" class="copy-button" data-copy aria-label="<?= h($label) ?>" hidden>
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" aria-hidden="true">
            <rect x="8" y="8" width="12" height="12" rx="2"/><path d="M16 4H6a2 2 0 0 0-2 2v10"/>
        </svg>
        <span class="copy-tooltip" aria-hidden="true">Копировать</span>
    </button>
    <?php
}

function snippet(string $language, string $code): void
{
    ?>
    <div class="code">
        <div class="code-bar"><span><?= h($language) ?></span><?php copyButton(); ?></div>
        <pre><code><?= h($code) ?></code></pre>
    </div>
    <?php
}

function siteStart(string $page): void
{
    header('Content-Type: text/html; charset=UTF-8');
    [$title, $description] = SITE_PAGES[$page];
    ?>
<!doctype html>
<html lang="ru">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="description" content="<?= h($description) ?>">
    <title><?= h($page === 'index' ? 'mukimov — библиотека для Python' : $title . ' · mukimov') ?></title>
    <link rel="stylesheet" href="style.css?v=<?= filemtime(__DIR__ . '/style.css') ?>">
    <link rel="icon" href="favicon.svg?v=<?= SITE_VERSION ?>" type="image/svg+xml">
    <script src="app.js?v=<?= filemtime(__DIR__ . '/app.js') ?>" defer></script>
</head>
<body>
<a class="skip" href="#main">К основному содержанию</a>
<header class="top">
    <div class="wrap top-inner">
        <a class="brand" href="index.php"><span aria-hidden="true">›_</span> mukimov</a>
        <nav aria-label="Основная навигация">
            <?php pageLink('start', 'Начать'); ?>
            <?php pageLink('api', 'API'); ?>
            <a href="<?= SITE_REPO ?>">GitHub ↗</a>
            <button type="button" id="theme-toggle" hidden>Чёрное на белом</button>
        </nav>
    </div>
</header>
    <?php
}

function docsStart(string $page, string $group, array $sections): void
{
    siteStart($page);
    [$title, $description] = SITE_PAGES[$page];
    ?>
<div class="wrap docs-shell">
    <aside class="docs-sidebar">
        <nav aria-label="Разделы сайта">
            <a class="version-label" href="releases.php">Документация <?= SITE_VERSION ?></a>
            <?php foreach (SITE_NAV as $label => $ids): ?>
                <p class="eyebrow"><?= h($label) ?></p>
                <?php foreach ($ids as $id): ?>
                    <a href="<?= h($id) ?>.php"<?= $id === $page ? ' aria-current="page"' : '' ?>><?= h(SITE_PAGES[$id][0]) ?></a>
                <?php endforeach; ?>
            <?php endforeach; ?>
        </nav>
    </aside>
    <main id="main" class="docs-main">
        <nav class="breadcrumbs" aria-label="Путь"><?php pageLink('index', 'Главная'); ?><span aria-hidden="true">/</span><span><?= h($group) ?></span></nav>
        <article>
            <header class="article-header">
                <h1><?= h($title) ?></h1>
                <p><?= h($description) ?></p>
            </header>
            <?php if ($sections): ?>
                <nav class="page-outline" aria-label="На этой странице">
                    <strong>На этой странице</strong>
                    <ul>
                        <?php foreach ($sections as $id => $label): ?>
                            <li><a href="#<?= h($id) ?>"><?= h($label) ?></a></li>
                        <?php endforeach; ?>
                    </ul>
                </nav>
            <?php endif;
}

function docsEnd(array $related): void
{
    ?>
            <nav class="related" aria-label="Читайте дальше">
                <h2>Читайте дальше</h2>
                <ul>
                    <?php foreach ($related as $id): ?>
                        <li><?php pageLink($id); ?><span><?= h(SITE_PAGES[$id][1]) ?></span></li>
                    <?php endforeach; ?>
                </ul>
            </nav>
        </article>
    </main>
</div>
    <?php
    siteEnd();
}

function siteEnd(): void
{
    ?>
<footer>
    <div class="wrap footer">
        <a class="footer-brand" href="index.php">mukimov</a>
        <span>Python 3.8+ · MIT</span>
        <?php pageLink('releases', 'Версия ' . SITE_VERSION); ?>
        <a href="<?= SITE_PYPI ?>">PyPI ↗</a>
        <a href="<?= SITE_REPO ?>">Исходный код ↗</a>
    </div>
</footer>
<div id="copy-toast" class="copy-toast" hidden aria-hidden="true">Скопировано</div>
<div id="copy-status" class="sr-only" role="status"></div>
</body>
</html>
    <?php
}
