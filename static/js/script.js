gsap.registerPlugin(ScrollTrigger);

// ── Navbar scroll shadow ──
window.addEventListener('scroll', () => {
    document.querySelector('.navbar').classList.toggle('scrolled', window.scrollY > 10);
});

// ── Page load: navbar + hero ──
const tl = gsap.timeline({ defaults: { ease: 'power3.out' } });

tl.from('.navbar', { y: -68, opacity: 0, duration: 0.7, clearProps: 'all' })
  .to('.hero-title',    { y: 0, opacity: 1, duration: 0.8 }, '-=0.3')
  .to('.hero-subtitle', { y: 0, opacity: 1, duration: 0.7 }, '-=0.55')
  .to('.hero-actions',  { y: 0, opacity: 1, duration: 0.6 }, '-=0.5')
  .to('.trust-strip',   { opacity: 1, duration: 0.6 }, '-=0.4');

// ── Subtle hero parallax ──
gsap.to('.hero-section', {
    backgroundPositionY: '30%',
    ease: 'none',
    scrollTrigger: {
        trigger: '.hero-section',
        start: 'top top',
        end: 'bottom top',
        scrub: 1.5
    }
});

// ── Product section scroll reveals ──
document.querySelectorAll('.product-section').forEach(section => {
    const textEls    = section.querySelectorAll('.product-text > *');
    const imgWrapper = section.querySelector('.image-wrapper');

    // Text: staggered slide-up fade
    gsap.from(textEls, {
        scrollTrigger: { trigger: section, start: 'top 78%', toggleActions: 'play none none reverse' },
        y: 32,
        opacity: 0,
        duration: 0.65,
        stagger: 0.1,
        ease: 'power2.out'
    });

    // Image: clean fade + gentle rise
    if (imgWrapper) {
        gsap.from(imgWrapper, {
            scrollTrigger: { trigger: section, start: 'top 78%', toggleActions: 'play none none reverse' },
            y: 40,
            opacity: 0,
            duration: 0.8,
            ease: 'power2.out'
        });
    }
});

// ── Image: subtle tilt on mouse move ──
document.querySelectorAll('.image-wrapper').forEach(wrap => {
    wrap.addEventListener('mousemove', e => {
        const r = wrap.getBoundingClientRect();
        const x = (e.clientX - r.left - r.width  / 2) / r.width;
        const y = (e.clientY - r.top  - r.height / 2) / r.height;
        gsap.to(wrap, { rotationY: x * 6, rotationX: -y * 6, duration: 0.4, ease: 'power1.out' });
    });
    wrap.addEventListener('mouseleave', () => {
        gsap.to(wrap, { rotationY: 0, rotationX: 0, duration: 0.6, ease: 'power2.out' });
    });
});

// ── Smooth scroll for anchor links ──
document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', e => {
        e.preventDefault();
        document.querySelectorAll('.nav-links a').forEach(l => l.classList.remove('active'));
        a.classList.add('active');
        const target = document.querySelector(a.getAttribute('href'));
        if (target) window.scrollTo({ top: target.offsetTop - 80, behavior: 'smooth' });
    });
});

// ── Theme Switcher ──
function applyTheme(theme) {
    const html = document.documentElement;
    if (theme === 'default') {
        html.removeAttribute('data-theme');
    } else {
        html.setAttribute('data-theme', theme);
    }
    // Update active option highlight
    document.querySelectorAll('.theme-option').forEach(opt => {
        opt.classList.toggle('active', opt.dataset.theme === theme);
    });
    // Update navbar icon
    const icon = document.getElementById('theme-icon');
    if (icon) {
        if (theme === 'dark')         icon.className = 'fas fa-moon';
        else if (theme === 'light')   icon.className = 'fas fa-sun';
        else                          icon.className = 'fas fa-circle-half-stroke';
    }
}

function setTheme(theme) {
    localStorage.setItem('theme', theme);
    applyTheme(theme);
    document.getElementById('theme-dropdown').classList.remove('open');
}

// Init on load
(function () {
    const saved = localStorage.getItem('theme') || 'default';
    applyTheme(saved);

    document.getElementById('theme-toggle-btn').addEventListener('click', function (e) {
        e.stopPropagation();
        document.getElementById('theme-dropdown').classList.toggle('open');
        document.getElementById('currency-dropdown').classList.remove('open');
    });

    document.addEventListener('click', function () {
        const dd = document.getElementById('theme-dropdown');
        if (dd) dd.classList.remove('open');
        const cd = document.getElementById('currency-dropdown');
        if (cd) cd.classList.remove('open');
    });
})();

// ── Currency (always INR) ──
const USD_TO_INR = 84;

/** Formats a USD amount always as INR ₹ */
function formatPrice(usd) {
    const amt = parseFloat(usd);
    return '₹' + Math.round(amt * USD_TO_INR).toLocaleString('en-IN');
}

// Step 1: Scan the DOM and wrap all $X.XX price values in tagged spans
function initPrices() {
    const priceRegex = /\$([\d,]+(?:\.\d+)?)/g;
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null);
    const nodes = [];
    let node;
    while ((node = walker.nextNode())) {
        // Skip navbar, scripts, and elements already processed
        const parent = node.parentElement;
        if (!parent) continue;
        if (parent.closest('#currency-switcher, .theme-switcher, script, style')) continue;
        if (parent.classList && parent.classList.contains('price-val')) continue;
        if (priceRegex.test(node.textContent)) nodes.push(node);
        priceRegex.lastIndex = 0;
    }
    nodes.forEach(textNode => {
        const frag = document.createDocumentFragment();
        let last = 0;
        const text = textNode.textContent;
        let m;
        priceRegex.lastIndex = 0;
        while ((m = priceRegex.exec(text)) !== null) {
            if (m.index > last) {
                frag.appendChild(document.createTextNode(text.slice(last, m.index)));
            }
            const span = document.createElement('span');
            span.className = 'price-val';
            span.dataset.usd = m[1];
            span.textContent = m[0];
            frag.appendChild(span);
            last = m.index + m[0].length;
        }
        if (last < text.length) frag.appendChild(document.createTextNode(text.slice(last)));
        textNode.parentNode.replaceChild(frag, textNode);
    });
}

// Step 2: Apply INR to all tagged price spans
function applyCurrency() {
    document.querySelectorAll('.price-val').forEach(el => {
        const usd = parseFloat(el.dataset.usd);
        el.textContent = '₹' + Math.round(usd * USD_TO_INR).toLocaleString('en-IN');
    });
}

function setCurrency() {} // kept for safety, no-op

// Init on DOMContentLoaded — always INR
document.addEventListener('DOMContentLoaded', function () {
    initPrices();
    applyCurrency();
});
