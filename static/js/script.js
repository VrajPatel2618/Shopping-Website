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
