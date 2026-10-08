// Permalinks for page sections, like the Recommendations page: a link icon beside each section heading on hover,
// which copies the section's address and puts it in the address bar without jumping the page.
// A section is any <section> or region with an id whose first heading is an h2.
document.addEventListener('DOMContentLoaded', () => {
  const LINK = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M6.5 9.5a3 3 0 0 0 4.2 0l2.3-2.3a3 3 0 0 0-4.2-4.2l-.8.8M9.5 6.5a3 3 0 0 0-4.2 0L3 8.8a3 3 0 0 0 4.2 4.2l.8-.8" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>';
  document.querySelectorAll('main :is(section, [role="region"])[id]').forEach(sec => {
    const h = sec.querySelector('h2'); if (!h || h.closest(':is(section, [role="region"])[id]') !== sec || h.classList.contains('sr-only') || h.querySelector('.sec-anchor')) return;
    h.insertAdjacentHTML('beforeend', `<a class="sec-anchor" href="#${sec.id}" data-id="${sec.id}" aria-label="Copy link to this section">${LINK}</a>`);
    sec.classList.add('has-anchor');
  });
  // Sections filled in by script aren't there when the browser first looks for the address's section, so go there now.
  const el = location.hash && document.getElementById(decodeURIComponent(location.hash.slice(1)));
  if (el) el.scrollIntoView({ block: 'start' });
  document.addEventListener('click', e => {
    const a = e.target.closest('.sec-anchor'); if (!a) return;
    e.preventDefault();
    const url = `${location.origin}${location.pathname}${location.search}#${a.dataset.id}`;
    history.replaceState(null, '', url);
    (navigator.clipboard ? navigator.clipboard.writeText(url) : Promise.reject()).then(() => {
      a.classList.add('copied'); a.setAttribute('aria-label', 'Link copied');
      setTimeout(() => { a.classList.remove('copied'); a.setAttribute('aria-label', 'Copy link to this section'); }, 1600);
    }, () => {});
  });
});
