// Atlas Pharma QMS — Client-side JavaScript

document.addEventListener('DOMContentLoaded', () => {
    // ── Tab Switching (with URL hash persistence) ───────────────────────
    const activateTab = (tabBtn) => {
        const group = tabBtn.closest('.tabs-wrapper');
        if (!group) return;
        group.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        group.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
        tabBtn.classList.add('active');
        const panel = group.querySelector(`#${tabBtn.dataset.tab}`);
        if (panel) panel.classList.add('active');
    };

    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            activateTab(tab);
            // Persist in URL hash so reloads restore the tab
            history.replaceState(null, '', '#' + tab.dataset.tab);
        });
    });

    // On page load, restore tab from URL hash if present
    if (window.location.hash) {
        const target = window.location.hash.slice(1);
        const tabBtn = document.querySelector(`.tab[data-tab="${target}"]`);
        if (tabBtn) activateTab(tabBtn);
    }

    // ── Auto-dismiss flash messages ──────────────────────────────────────
    document.querySelectorAll('.flash-msg').forEach(msg => {
        setTimeout(() => {
            msg.style.transition = 'opacity 0.4s, transform 0.4s';
            msg.style.opacity = '0';
            msg.style.transform = 'translateX(100%)';
            setTimeout(() => msg.remove(), 400);
        }, 4000);
    });

    // ── Smooth reveal on scroll ──────────────────────────────────────────
    const observerOptions = { threshold: 0.1, rootMargin: '0px 0px -40px 0px' };
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    document.querySelectorAll('.card, .product-card, .team-card, .value-card, .kpi-card, .review-card, .partner-card, .capa-card').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
        observer.observe(el);
    });

    // ── Confirm actions ──────────────────────────────────────────────────
    document.querySelectorAll('form[data-confirm]').forEach(form => {
        form.addEventListener('submit', (e) => {
            if (!confirm(form.dataset.confirm)) {
                e.preventDefault();
            }
        });
    });
});
