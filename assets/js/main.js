// Przedszkole św. Jacka w Straszynie — skrypty wspólne dla wszystkich stron

// menu mobilne
const burger = document.getElementById('burger');
const menu = document.getElementById('menu');
if (burger && menu) {
  const setOpen = open => {
    menu.classList.toggle('open', open);
    burger.setAttribute('aria-expanded', open);
    burger.setAttribute('aria-label', open ? 'Zamknij menu' : 'Otwórz menu');
  };
  burger.addEventListener('click', () => setOpen(!menu.classList.contains('open')));
  menu.addEventListener('click', e => { if (e.target.closest('a')) setOpen(false); });
  // kliknięcie poza nagłówkiem zamyka menu
  document.addEventListener('click', e => {
    if (menu.classList.contains('open') && !e.target.closest('header')) setOpen(false);
  });
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && menu.classList.contains('open')) { setOpen(false); burger.focus(); }
  });
  // po obróceniu tabletu do szerokiego układu menu mobilne nie zostaje otwarte
  matchMedia('(min-width: 881px)').addEventListener('change', e => { if (e.matches) setOpen(false); });
}

// zwijane fragmenty (.fold) — CSS zwija je tylko na telefonach
document.querySelectorAll('[data-fold]').forEach(fold => {
  const btn = fold.querySelector('.fold-btn');
  const more = btn.textContent;
  const setOpen = open => {
    fold.classList.toggle('open', open);
    btn.setAttribute('aria-expanded', open);
    btn.textContent = open ? (btn.dataset.less || 'Zwiń') : more;
  };
  btn.addEventListener('click', () => {
    const open = !fold.classList.contains('open');
    setOpen(open);
    // po zwinięciu długiego bloku wróć do jego początku, żeby nie „zgubić” miejsca
    if (!open && fold.getBoundingClientRect().top < 0) fold.scrollIntoView({ block: 'start' });
  });
  // fokus z klawiatury wewnątrz zwiniętej treści rozwija ją
  fold.addEventListener('focusin', e => { if (!btn.contains(e.target)) setOpen(true); });
});

// <details data-open-desktop> — rozwinięte na większych ekranach, na telefonie startują zwinięte
if (matchMedia('(max-width: 640px)').matches) {
  document.querySelectorAll('details[data-open-desktop]').forEach(d => d.removeAttribute('open'));
}

// przycisk „do góry” pokazuje się po przewinięciu ponad ekran
const toTop = document.querySelector('.to-top');
if (toTop) {
  const update = () => toTop.classList.toggle('show', scrollY > innerHeight * 1.2);
  addEventListener('scroll', update, { passive: true });
  update();
}

// łagodne pojawianie się bloków .reveal przy przewijaniu
const reveals = document.querySelectorAll('.reveal');
if ('IntersectionObserver' in window) {
  const io = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
    });
  }, { threshold: .12 });
  reveals.forEach(el => io.observe(el));
} else {
  reveals.forEach(el => el.classList.add('in'));
}

// filtry galerii
const filters = document.querySelectorAll('#filters .filter');
if (filters.length) {
  const tiles = document.querySelectorAll('#gallery .tile');
  filters.forEach(f => f.addEventListener('click', () => {
    filters.forEach(x => {
      x.classList.toggle('active', x === f);
      x.setAttribute('aria-pressed', x === f);
    });
    const cat = f.dataset.cat;
    tiles.forEach(t => { t.hidden = cat !== 'all' && t.dataset.cat !== cat; });
  }));
}
