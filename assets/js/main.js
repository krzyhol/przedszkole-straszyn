// Przedszkole św. Jacka w Straszynie — skrypty wspólne dla wszystkich stron

// menu mobilne
const burger = document.getElementById('burger');
const menu = document.getElementById('menu');
if (burger && menu) {
  const setOpen = open => {
    menu.classList.toggle('open', open);
    burger.setAttribute('aria-expanded', open);
  };
  burger.addEventListener('click', () => setOpen(!menu.classList.contains('open')));
  menu.addEventListener('click', e => { if (e.target.closest('a')) setOpen(false); });
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && menu.classList.contains('open')) { setOpen(false); burger.focus(); }
  });
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
