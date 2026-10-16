// One dead end: what it is, the runs it stopped (with what happened in each), the requests it came up in, and the
// ideas in the recommendations that would clear it.
(function () {
  const R = window.REAL, { D, esc } = R, $p = document.getElementById('page');
  const id = new URLSearchParams(location.search).get('id') || '', d = R.deadEnds[id];
  if (!d) return R.missing($p, 'dead end', id);
  document.title = `${id} ${d.title} · Building with WordPress · Agent Benchmarks`;
  const hit = R.ours.filter(r => Object.values(r.checks).some(c => R.failing(c) && (c.dead_ends || []).includes(id)));
  const pool = d.setups ? R.ours.filter(r => d.setups.includes(r.kind)) : R.ours;
  const w = d.write_up || {};
  const seen = hit.map(r => { const c = Object.values(r.checks).find(c => R.failing(c) && (c.dead_ends || []).includes(id));
    return `<li>${R.link.run(r)}, ${R.link.request(R.requests[r.request])}<small>${esc(c.what_stopped || c.detail || '')}</small>${c.quote ? `<small><q>${esc(c.quote)}</q></small>` : ''}</li>`; }).join('');
  const reqs = [...new Set(hit.map(r => r.request))].map(q => R.link.request(R.requests[q])).join(', ');
  const ideas = R.ideasFor(id);
  $p.innerHTML = `<a class="go back" href="./">All dead ends</a>
    <h1 class="title">${esc(d.title)}</h1>
    <p class="run-sub"><span>${id}</span><span>${hit.length} of ${pool.length} runs with or without the MCP adapter</span></p>
    <dl class="run-facts">
      ${R.fact('What the owner sees', esc(d.seen))}
      ${R.fact('What happens', esc(d.what || w.what_happens || ''))}
      ${R.fact('Ideas that would clear it', ideas.length ? `<ul class="p-list">${ideas.map(x => `<li><a href="idea?id=${x.id}">${esc(x.title)}</a></li>`).join('')}</ul>` : '')}
      ${R.fact('Came up in', reqs)}
      ${R.fact('Runs it stopped', hit.length ? `<ul class="p-list">${seen}</ul>` : 'None in this batch.')}
    </dl>`;
})();
