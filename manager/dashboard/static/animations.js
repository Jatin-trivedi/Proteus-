/**
 * JOCKY Manager — Animations & Micro-interactions
 * Lenis smooth scroll · GSAP ScrollTrigger · Spotlight hover · Log stagger
 */
(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', () => {
    // ══════════════════════════════════════════════════════════════════════════
    // 1. Lenis Smooth Scroll + GSAP Sync
    // ══════════════════════════════════════════════════════════════════════════
    if (typeof Lenis !== 'undefined') {
      const lenis = new Lenis({
        duration: 0.9,
        smoothWheel: true,
        syncTouch: false
      });

      if (typeof ScrollTrigger !== 'undefined') {
        gsap.registerPlugin(ScrollTrigger);
        lenis.on('scroll', ScrollTrigger.update);
        gsap.ticker.add((time) => lenis.raf(time * 1000));
        gsap.ticker.lagSmoothing(0);
      } else {
        function rafLoop(time) { lenis.raf(time); requestAnimationFrame(rafLoop); }
        requestAnimationFrame(rafLoop);
      }
      window.__lenis = lenis;
    }

    // ══════════════════════════════════════════════════════════════════════════
    // 2. Page Load Entry Sequence
    // ══════════════════════════════════════════════════════════════════════════
    if (typeof gsap !== 'undefined') {
      const targets = document.querySelectorAll('.animate-on-load, #main-nav');
      if (targets.length > 0) {
        gsap.from(targets, {
          opacity: 0,
          y: 20,
          stagger: 0.08,
          duration: 0.6,
          ease: 'power2.out'
        });
      }
    }

    // ══════════════════════════════════════════════════════════════════════════
    // 3. Spotlight Border Effect (cursor-relative radial glow on cards)
    // ══════════════════════════════════════════════════════════════════════════
    function initSpotlightCards() {
      const cards = document.querySelectorAll('.soc-card, .metric-card, .spotlight-card');
      cards.forEach((card) => {
        card.style.position = 'relative';
        card.style.overflow = 'hidden';

        const light = document.createElement('div');
        light.className = 'card-spotlight';
        light.style.cssText = [
          'position:absolute', 'inset:0', 'pointer-events:none',
          'opacity:0', 'transition:opacity 0.3s ease',
          'border-radius:inherit', 'z-index:0',
        ].join(';');
        card.prepend(light);

        card.addEventListener('mousemove', (e) => {
          const rect = card.getBoundingClientRect();
          const x = e.clientX - rect.left;
          const y = e.clientY - rect.top;
          light.style.background = `radial-gradient(circle at ${x}px ${y}px, rgba(6,182,212,0.18) 0%, rgba(16,185,129,0.06) 40%, transparent 65%)`;
          light.style.opacity = '1';
        });

        card.addEventListener('mouseleave', () => {
          light.style.opacity = '0';
        });
      });
    }

    // ══════════════════════════════════════════════════════════════════════════
    // 4. Scroll-Triggered Stagger (any [data-stagger] parent)
    // ══════════════════════════════════════════════════════════════════════════
    function initScrollStagger() {
      if (typeof gsap === 'undefined' || typeof ScrollTrigger === 'undefined') return;
      document.querySelectorAll('[data-stagger]').forEach((container) => {
        const children = Array.from(container.children);
        if (!children.length) return;
        gsap.set(children, { y: 24, opacity: 0 });
        ScrollTrigger.create({
          trigger: container,
          start: 'top 88%',
          once: true,
          onEnter() {
            gsap.to(children, {
              y: 0, opacity: 1,
              duration: 0.5, stagger: 0.065, ease: 'power2.out',
            });
          },
        });
      });
    }

    // ══════════════════════════════════════════════════════════════════════════
    // 5. Architecture SVG Arrow ScrollTrigger Sequence
    // ══════════════════════════════════════════════════════════════════════════
    function initArchFlow() {
      if (typeof gsap === 'undefined' || typeof ScrollTrigger === 'undefined') return;

      const archSection = document.getElementById('arch-flow');
      if (!archSection) return;

      const nodes = archSection.querySelectorAll('[data-arch-node]');
      const arrows = archSection.querySelectorAll('.arch-arrow');

      if (nodes.length === 0) return;

      gsap.set(nodes, { y: 30, opacity: 0 });
      arrows.forEach((a) => {
        const len = a.getTotalLength ? a.getTotalLength() : 200;
        gsap.set(a, { strokeDasharray: len, strokeDashoffset: len });
      });

      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: archSection,
          start: 'top 70%',
          end: 'bottom 30%',
          toggleActions: 'play none none reset',
        },
      });

      nodes.forEach((node, i) => {
        tl.to(node, { y: 0, opacity: 1, duration: 0.5, ease: 'power2.out' }, i === 0 ? '+=0' : '-=0.15');

        tl.fromTo(node, { filter: 'drop-shadow(0 0 0px rgba(6,182,212,0))' },
          { filter: 'drop-shadow(0 0 12px rgba(6,182,212,0.7))', duration: 0.3, yoyo: true, repeat: 1 },
          '<0.3'
        );

        if (arrows[i]) {
          tl.to(arrows[i], { strokeDashoffset: 0, duration: 0.5, ease: 'power1.inOut', onComplete: () => {
              gsap.set(arrows[i], { strokeDasharray: "6 4" });
              gsap.fromTo(arrows[i], 
                  { strokeDashoffset: 0 }, 
                  { strokeDashoffset: -20, duration: 1.5, ease: "none", repeat: -1 }
              );
          }}, '<0.1');
        }
      });
    }

    // ══════════════════════════════════════════════════════════════════════════
    // 6. Forensics Log Page: Terminal Stagger
    // ══════════════════════════════════════════════════════════════════════════
    function initLogPageAnimations() {
      window.animateLogRows = function (container) {
        const rows = container ? container.querySelectorAll('.log-row, tr') : [];
        if (!rows.length || typeof gsap === 'undefined') return;
        gsap.from(Array.from(rows), {
          opacity: 0, x: -15,
          stagger: 0.03, duration: 0.4, ease: 'power2.out',
          clearProps: 'transform,opacity',
        });
      };
    }

    // ══════════════════════════════════════════════════════════════════════════
    // 7. GSAP Counter
    // ══════════════════════════════════════════════════════════════════════════
    function initCounters() {
      if (typeof gsap === 'undefined' || typeof ScrollTrigger === 'undefined') return;
      document.querySelectorAll('.gsap-counter').forEach((el) => {
        const target = parseFloat(el.dataset.target || el.innerText) || 0;
        const isFloat = String(target).includes('.');
        ScrollTrigger.create({
          trigger: el, start: 'top 92%', once: true,
          onEnter() {
            const proxy = { val: 0 };
            gsap.to(proxy, {
              val: target, duration: 1.7, ease: 'power2.out',
              onUpdate() { el.innerText = isFloat ? proxy.val.toFixed(1) : Math.floor(proxy.val); },
            });
          },
        });
      });
    }

    window.animateTableRows = function (tbody) {
      if (!tbody || typeof gsap === 'undefined') return;
      const rows = Array.from(tbody.querySelectorAll('tr'));
      if (!rows.length) return;
      gsap.fromTo(rows,
        { y: 12, opacity: 0 },
        { y: 0, opacity: 1, duration: 0.35, stagger: 0.04, ease: 'power2.out' }
      );
    };

    window.animateToastIn = function (el) {
      if (!el || typeof gsap === 'undefined') return;
      gsap.fromTo(el,
        { x: 60, opacity: 0, scale: 0.95 },
        { x: 0, opacity: 1, scale: 1, duration: 0.38, ease: 'back.out(1.6)' }
      );
    };

    function initCardHover() {
      if (typeof gsap === 'undefined') return;
      document.querySelectorAll('.soc-card, .metric-card').forEach((card) => {
        card.addEventListener('mouseenter', () =>
          gsap.to(card, { scale: 1.018, duration: 0.25, ease: 'power1.out' })
        );
        card.addEventListener('mouseleave', () =>
          gsap.to(card, { scale: 1, duration: 0.32, ease: 'power2.out' })
        );
      });
    }

    // ══════════════════════════════════════════════════════════════════════════
    // 8. Dashboard SPA Toggle
    // ══════════════════════════════════════════════════════════════════════════
    function initDashboardToggle() {
      const dashLink = document.getElementById('nav-dashboard-link');
      const dashView = document.getElementById('dashboard-view');
      const pageContent = document.getElementById('page-content');
      if (!dashLink || !dashView || !pageContent) return;

      function showDashboard(e) {
        if(e) e.preventDefault();
        dashView.style.display = 'block';
        pageContent.style.display = 'none';
        if (typeof window.loadFleetDashboard === 'function') window.loadFleetDashboard();

        // Update nav active states
        document.querySelectorAll('.nav-link').forEach(n => {
          n.classList.remove('text-emerald', 'bg-emerald/10', 'border-emerald/20');
          n.classList.add('text-slate-600', 'border-transparent');
        });
        dashLink.classList.remove('text-slate-600', 'border-transparent');
        dashLink.classList.add('text-emerald', 'bg-emerald/10', 'border-emerald/20');

        // GSAP animate
        if (typeof gsap !== 'undefined') {
          gsap.fromTo("#dashboard-view .soc-card", 
            { opacity: 0, y: 15 },
            { opacity: 1, y: 0, stagger: 0.05, duration: 0.4, ease: "power2.out" }
          );
          
          document.querySelectorAll('#dashboard-view .gsap-counter').forEach(el => {
            const target = parseFloat(el.dataset.target) || 0;
            const isFloat = String(target).includes('.');
            const proxy = { val: 0 };
            gsap.to(proxy, {
              val: target, duration: 1.7, ease: 'power2.out',
              onUpdate() { el.innerText = isFloat ? proxy.val.toFixed(1) : Math.floor(proxy.val); }
            });
          });
        }
      }

      dashLink.addEventListener('click', showDashboard);

      // Show by default if hash is #dashboard or if path is exactly /dashboard
      if (window.location.hash === '#dashboard' || window.location.pathname === '/dashboard' || window.location.pathname === '/') {
        showDashboard();
      } else {
        dashView.style.display = 'none';
        pageContent.style.display = 'block';
      }
    }

    // ══════════════════════════════════════════════════════════════════════════
    // Boot sequence
    // ══════════════════════════════════════════════════════════════════════════
    initSpotlightCards();
    initScrollStagger();
    initArchFlow();
    initLogPageAnimations();
    initCounters();
    initCardHover();
    initDashboardToggle();
  });

})();
