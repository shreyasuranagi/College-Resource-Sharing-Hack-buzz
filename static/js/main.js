// Neural Breach — Main JS

document.addEventListener('DOMContentLoaded', () => {

  // ─── NAV HAMBURGER ─────────────────────────────
  const toggle = document.getElementById('navToggle');
  const links  = document.querySelector('.nav-links');
  if (toggle && links) {
    toggle.addEventListener('click', () => links.classList.toggle('open'));
  }

  // ─── AUTO DISMISS FLASHES ──────────────────────
  document.querySelectorAll('.flash').forEach(el => {
    setTimeout(() => {
      el.style.transition = 'opacity 0.5s';
      el.style.opacity = '0';
      setTimeout(() => el.remove(), 500);
    }, 5000);
  });

  // ─── FILE DROP ENHANCEMENT ─────────────────────
  const drop = document.getElementById('fileDrop');
  if (drop) {
    drop.addEventListener('drop', e => {
      e.preventDefault();
      const f = e.dataTransfer.files[0];
      if (f) {
        const inp = document.getElementById('fileInput');
        const dt  = new DataTransfer();
        dt.items.add(f);
        inp.files = dt.files;
        inp.dispatchEvent(new Event('change'));
      }
    });
  }

  // ─── STAR RATING HOVER ─────────────────────────
  document.querySelectorAll('.star-rating').forEach(sr => {
    const labels = sr.querySelectorAll('label');
    // Labels are in reverse order (5,4,3,2,1) due to CSS trick
    // hover handled via pure CSS
  });

  // ─── FADE UP OBSERVER ──────────────────────────
  const obs = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.style.opacity = '1';
        e.target.style.transform = 'translateY(0)';
      }
    });
  }, { threshold: 0.05 });

  document.querySelectorAll('.fade-up').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(20px)';
    el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
    obs.observe(el);
  });

  // ─── GLITCH TERMINAL EFFECT ON HERO ───────────
  const glitches = document.querySelectorAll('.glitch');
  glitches.forEach(el => {
    el.dataset.text = el.textContent;
  });

  // ─── CONFIRM DELETE ────────────────────────────
  document.querySelectorAll('[data-confirm]').forEach(el => {
    el.addEventListener('click', e => {
      if (!confirm(el.dataset.confirm)) e.preventDefault();
    });
  });

  // ─── SEARCH: submit on filter change ──────────
  const filterSelects = document.querySelectorAll('.search-filters select');
  filterSelects.forEach(sel => {
    // Don't auto-submit, let user click Apply
  });

  // ─── TAG INPUT HELPER ──────────────────────────
  const tagInput = document.getElementById('tags');
  if (tagInput) {
    tagInput.addEventListener('keydown', e => {
      if (e.key === 'Enter') {
        e.preventDefault();
        const val = tagInput.value.trim();
        if (val && !val.endsWith(',')) {
          tagInput.value = val + ', ';
        }
      }
    });
  }

  // ─── TYPING EFFECT FOR HERO TITLE ─────────────
  const heroTitle = document.querySelector('.hero-title .t2');
  if (heroTitle) {
    const text = heroTitle.textContent;
    heroTitle.textContent = '';
    let i = 0;
    const type = () => {
      if (i < text.length) {
        heroTitle.textContent += text[i++];
        setTimeout(type, 80);
      }
    };
    setTimeout(type, 600);
  }

  // ─── LIVE CLOCK IN FOOTER ─────────────────────
  const statusEl = document.querySelector('.footer-status');
  if (statusEl) {
    setInterval(() => {
      const now = new Date();
      const t = now.toTimeString().slice(0, 8);
      statusEl.innerHTML = `<span class="status-dot"></span> ${t} ONLINE`;
    }, 1000);
  }

  // ─── RESOURCE CARD RIPPLE ─────────────────────
  document.querySelectorAll('.resource-card').forEach(card => {
    card.addEventListener('click', function(e) {
      const link = this.querySelector('a');
      if (link && e.target.tagName !== 'A' && e.target.tagName !== 'BUTTON') {
        link.click();
      }
    });
  });

  console.log('%c⬡ NEURAL BREACH ONLINE', 'color:#00ffc8; font-family:monospace; font-size:1.2rem; font-weight:bold;');
  console.log('%cYugastr 2026 Hackathon', 'color:#ff2d78; font-family:monospace;');
});
