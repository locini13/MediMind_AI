/* ═══════════════════════════════════════════════════════════
   MediMind AI — Main Application Entry Point
   Initializes all modules and handles global interactions
   ═══════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {
    // Initialize all modules
    Chat.init();
    VoiceHandler.init();
    ImageHandler.init();

    // ── Sidebar Toggle (Mobile) ──
    const sidebar = document.getElementById('sidebar');
    const menuBtn = document.getElementById('menu-btn');
    const sidebarCloseBtn = document.getElementById('sidebar-close-btn');

    // Create overlay for mobile sidebar
    const overlay = document.createElement('div');
    overlay.className = 'sidebar-overlay';
    document.body.appendChild(overlay);

    function openSidebar() {
        sidebar.classList.add('open');
        overlay.classList.add('show');
    }

    function closeSidebar() {
        sidebar.classList.remove('open');
        overlay.classList.remove('show');
    }

    if (menuBtn) menuBtn.addEventListener('click', openSidebar);
    if (sidebarCloseBtn) sidebarCloseBtn.addEventListener('click', closeSidebar);
    overlay.addEventListener('click', closeSidebar);

    // ── Lightbox ──
    const lightbox = document.getElementById('lightbox');
    const lightboxClose = document.getElementById('lightbox-close');

    if (lightboxClose) {
        lightboxClose.addEventListener('click', () => {
            lightbox.style.display = 'none';
        });
    }

    if (lightbox) {
        lightbox.addEventListener('click', (e) => {
            if (e.target === lightbox) {
                lightbox.style.display = 'none';
            }
        });
    }

    // ── Keyboard Shortcuts ──
    document.addEventListener('keydown', (e) => {
        // Escape to close lightbox or sidebar
        if (e.key === 'Escape') {
            if (lightbox && lightbox.style.display !== 'none') {
                lightbox.style.display = 'none';
            } else {
                closeSidebar();
            }
        }

        // Ctrl+N for new conversation
        if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
            e.preventDefault();
            Chat.newSession();
        }
    });

    // ── Focus input on page load ──
    const messageInput = document.getElementById('message-input');
    if (messageInput) {
        messageInput.focus();
    }

    console.log(
        '%c🧠 MediMind AI %cInitialized',
        'color: #06b6d4; font-size: 16px; font-weight: bold;',
        'color: #10b981; font-size: 14px;'
    );
});
