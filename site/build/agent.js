// One agent: how it did on WordPress's own routes, by need and request, what stopped it, what it told owners
// wrongly and what it handled well (short checked quotes), and its runs.
(function () {
  const R = window.REAL, { D, esc } = R, $p = document.getElementById('page');
  const id = new URLSearchParams(location.search).get('id') || '', a = R.agents[id];
  if (!a) return R.missing($p, 'agent', id);
  document.title = `${a.name} in ${a.harness} · Building with WordPress · Agent Benchmarks`;
  const rs = R.ours.filter(r => r.agent === id), all = D.runs.filter(r => r.agent === id);
  const row = (label, x) => `<tr><td>${label}</td><td class="num">${R.done(x.filter(r => r.kind === 'base'))} of ${x.filter(r => r.kind === 'base').length}</td><td class="num">${R.done(x.filter(r => r.kind === 'official'))} of ${x.filter(r => r.kind === 'official').length}</td></tr>`;
  const causes = {}; rs.filter(r => !r.success_within).forEach(r => new Set(Object.values(r.checks).filter(c => R.failing(c) && c.cause).map(c => c.cause)).forEach(k => { causes[k] = (causes[k] || 0) + 1; }));
  const quotes = key => rs.flatMap(r => (r[key] || []).map(n => `<li>${esc(n.what)}<small><q>${esc(n.quote)}</q> ${R.link.run(r)}</small></li>`)).slice(0, 8).join('');
  $p.innerHTML = `<a class="go back" href="./">Data</a>
    <h1 class="title">${esc(a.name)} in ${esc(a.harness)}</h1>
    <p class="run-sub"><span>${R.done(rs)} of ${rs.length} runs completed, with or without the MCP adapter</span><span>${esc(D.batch.name.split(",")[0])} batch</span></p>
    <dl class="run-facts">
      ${R.fact('Completed', `<table class="p-table"><thead><tr><th></th><th class="num">No MCP adapter installed</th><th class="num">${R.ADAPTER}</th></tr></thead><tbody>${row('All prompts', rs)}${D.needs.map(n => row(esc(n.name), rs.filter(r => r.need === n.id))).join('')}</tbody></table>`)}
      ${R.fact('What stopped it', `<ul class="p-list">${Object.entries(causes).sort((x, y) => y[1] - x[1]).map(([k, n]) => `<li><a href="runs?agent=${id}&amp;cause=${k}">${esc(R.CAUSE[k] || k)}</a><small>${n} ${n === 1 ? 'run' : 'runs'}</small></li>`).join('')}</ul>`)}
      ${R.fact('Told owners wrongly', quotes('told_wrong') ? `<ul class="p-list">${quotes('told_wrong')}</ul>` : '', 'Things that were wrong or that the owner couldn’t use, quoted from the runs.')}
      ${R.fact('Handled well', quotes('handled_well') ? `<ul class="p-list">${quotes('handled_well')}</ul>` : '', 'What the checks don’t credit, quoted from the runs.')}
      ${R.fact('Runs', R.runsTable(all))}
    </dl>`;
})();
