/* ═══════════════════════════════════════════════════════════
   MediMind AI — Theme Manager (Dark/Light Mode)
   ═══════════════════════════════════════════════════════════ */

const ThemeManager = {
    STORAGE_KEY: 'medimind-theme',

    init() {
        const saved = localStorage.getItem(this.STORAGE_KEY) || 'dark';
        this.setTheme(saved, false);

        const toggle = document.getElementById('theme-toggle');
        if (toggle) {
            toggle.addEventListener('click', () => this.toggle());
        }
    },

    setTheme(theme, animate = true) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem(this.STORAGE_KEY, theme);

        const label = document.getElementById('theme-label');
        if (label) {
            label.textContent = theme === 'dark' ? 'Dark Mode' : 'Light Mode';
        }
    },

    toggle() {
        const current = document.documentElement.getAttribute('data-theme');
        const next = current === 'dark' ? 'light' : 'dark';
        this.setTheme(next);
    },

    get current() {
        return document.documentElement.getAttribute('data-theme') || 'dark';
    }
};

// Initialize immediately
ThemeManager.init();
