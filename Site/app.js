const status = document.querySelector('#copy-status');
const copyToast = document.querySelector('#copy-toast');
let toastTimeout;

const themeToggle = document.querySelector('#theme-toggle');
if (themeToggle) {
    const themeKey = 'mukimov-theme';
    let theme = 'dark';
    try {
        if (localStorage.getItem(themeKey) === 'light') theme = 'light';
    } catch {
        // Theme switching still works without storage.
    }

    const applyTheme = () => {
        document.documentElement.dataset.theme = theme;
        themeToggle.textContent = theme === 'dark' ? 'Чёрное на белом' : 'Белое на чёрном';
    };
    applyTheme();
    themeToggle.hidden = false;
    themeToggle.addEventListener('click', () => {
        theme = theme === 'dark' ? 'light' : 'dark';
        applyTheme();
        try {
            localStorage.setItem(themeKey, theme);
        } catch {
            // Keep the selection for this page.
        }
    });
}

document.addEventListener('copy', (event) => {
    if (!event.defaultPrevented) showCopyToast();
});

function showCopyToast() {
    clearTimeout(toastTimeout);
    copyToast.hidden = false;
    status.textContent = 'Текст скопирован в буфер обмена.';
    toastTimeout = setTimeout(() => {
        copyToast.hidden = true;
        status.textContent = '';
    }, 2200);
}
function selectCode(code) {
    const selection = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents(code);
    selection.removeAllRanges();
    selection.addRange(range);
}

const hashLevel = document.querySelector('#hash-level');
const hashExample = document.querySelector('#hash-example code');

if (hashLevel && hashExample) {
    const example = hashExample.textContent;
    document.querySelector('#hash-options').hidden = false;
    const updateHashExample = () => {
        hashExample.textContent = example
            .replace('verify_password, low', `verify_password, ${hashLevel.value}`)
            .replace('level=low', `level=${hashLevel.value}`);
    };
    hashLevel.addEventListener('change', updateHashExample);
    updateHashExample();
}

for (const button of document.querySelectorAll('[data-copy]')) {
    const code = button.closest('.code').querySelector('code');
    const tooltip = button.querySelector('.copy-tooltip');
    let reset;
    button.hidden = false;
    button.addEventListener('click', async () => {
        clearTimeout(reset);
        status.textContent = '';
        try {
            if (navigator.clipboard?.writeText) {
                await navigator.clipboard.writeText(code.textContent);
            } else {
                selectCode(code);
                if (!document.execCommand('copy')) throw new Error('Clipboard unavailable');
                window.getSelection().removeAllRanges();
            }
            tooltip.textContent = 'Скопировано';
            showCopyToast();
        } catch {
            selectCode(code);
            tooltip.textContent = 'Текст выделен';
            status.textContent = 'Текст выделен. Нажмите Ctrl+C или Command+C.';
        }
        reset = setTimeout(() => { tooltip.textContent = 'Копировать'; }, 2200);
    });
}

const apiFilter = document.querySelector('#api-filter');
if (apiFilter) {
    const entries = [...document.querySelectorAll('[data-api-entry]')];
    const status = document.querySelector('#api-status');
    const updateApiFilter = () => {
        const query = apiFilter.value.trim().toLowerCase();
        let matches = 0;
        for (const entry of entries) {
            entry.hidden = query !== '' && !entry.textContent.toLowerCase().includes(query);
            if (!entry.hidden) matches++;
        }
        status.textContent = query ? (matches ? `Найдено: ${matches}` : 'Ничего не найдено') : '';
    };
    document.querySelector('#api-search').hidden = false;
    apiFilter.addEventListener('input', updateApiFilter);
    updateApiFilter();
}
