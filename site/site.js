// Shared behaviour for the design system's components.

// Callouts: position each label under its segment and stack colliding labels in rows.
// Labels left of centre extend right from their line; labels right of centre extend left.
// Each side is placed in the order that keeps a deeper line from passing through a label above it.
function layoutCallouts() {
  document.querySelectorAll('.callouts').forEach(box => {
    const width = box.clientWidth, gap = 12;
    const items = [...box.querySelectorAll('.callout')].map(el => {
      const x = parseFloat(el.dataset.x) / 100 * width;
      const anchor = x < width / 2 ? 'left' : 'right';
      el.dataset.anchor = anchor;
      return { el, x, anchor, w: el.offsetWidth };
    });
    const rows = [], placed = [];
    // A row is free if no label already in it overlaps, and no line running down past it
    // (from a label placed in a deeper row) would pass through this label.
    const free = (r, from, to) =>
      !(rows[r] || []).some(([a, b]) => from < b + gap && to > a - gap) &&
      !placed.some(p => p.row > r && p.x > from - gap / 2 && p.x < to + gap / 2);
    const place = list => list.forEach(it => {
      const from = it.anchor === 'left' ? it.x : it.x - it.w, to = from + it.w;
      let r = 0;
      while (!free(r, from, to)) r++;
      (rows[r] = rows[r] || []).push([from, to]);
      placed.push({ x: it.x, row: r });
      it.el.style.setProperty('--row', r);
      it.el.style.left = it.anchor === 'left' ? it.x + 'px' : '';
      it.el.style.right = it.anchor === 'right' ? (width - it.x) + 'px' : '';
    });
    // Right-anchored labels extend left, so place them left to right; left-anchored, right to left.
    place(items.filter(i => i.anchor === 'right').sort((a, b) => a.x - b.x));
    place(items.filter(i => i.anchor === 'left').sort((a, b) => b.x - a.x));
    box.style.height = (10 + rows.length * 22) + 'px';
  });
}
// Share bars: one 100% bar from [category, label, percent] rows. Every category keeps its
// element, in a fixed order, so switching views animates widths instead of redrawing.
// A segment carries its label when the label fits inside it; otherwise it gets a callout.
const SHARE_ORDER = ['wp', 'code', 'cms', 'hosted', 'shop'];
const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)');
const shareDuration = () => (reduceMotion.matches ? 0 : 450);
const measureCtx = document.createElement('canvas').getContext('2d');

function renderShare(share, segs, title, instant) {
  share._share = [segs, title];
  const barEl = share.querySelector('.share-bar');
  const callouts = share.querySelector('.callouts');
  const first = !barEl.children.length;
  if (first) barEl.innerHTML = SHARE_ORDER.map(c => `<span class="seg seg-${c} zero" data-c="${c}" style="width:0%"><span class="seg-t"></span></span>`).join('');
  const now = first || instant || !shareDuration();
  const width = barEl.clientWidth;
  const byCat = Object.fromEntries(segs.map(r => [r[0], r]));
  let x = 0, calls = '';
  SHARE_ORDER.forEach(c => {
    const el = barEl.querySelector(`[data-c="${c}"]`);
    const [, name = '', v = 0] = byCat[c] || [];
    const label = `${name} ${v}%`;
    measureCtx.font = getComputedStyle(el).font;
    const fits = v > 0 && measureCtx.measureText(label).width + 24 <= v / 100 * width;
    el.style.width = v + '%';
    el.classList.toggle('zero', !v);
    el.classList.toggle('labelled', fits);
    el.title = v ? label : '';
    const text = el.querySelector('.seg-t');
    if (now) text.textContent = fits ? label : '';
    else {
      text.style.opacity = 0;
      setTimeout(() => { text.textContent = fits ? label : ''; text.style.opacity = ''; }, shareDuration());
    }
    if (v && !fits) calls += `<span class="callout${c === 'wp' ? ' callout-wp' : ''}" data-x="${x + v / 2}">${name} <b>${v}%</b></span>`;
    x += v;
  });
  barEl.setAttribute('aria-label', `${title}: ` + segs.map(([, n, v]) => `${n} ${v}%`).join(', '));
  if (now) { callouts.innerHTML = calls; layoutCallouts(); return; }
  callouts.classList.add('fading');
  setTimeout(() => { callouts.innerHTML = calls; layoutCallouts(); callouts.classList.remove('fading'); }, shareDuration());
}

layoutCallouts();
// Whether a label fits depends on width, so re-render share bars on resize.
addEventListener('resize', () => {
  document.querySelectorAll('.share').forEach(share => share._share && renderShare(share, ...share._share, true));
  layoutCallouts();
});
if (document.fonts) document.fonts.ready.then(layoutCallouts);
