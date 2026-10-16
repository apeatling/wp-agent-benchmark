// Shared by the Building pages that read the real runs (site/data/build.js, from `wpab site build`): names,
// lookups and links, so every run, request, agent and dead end has one page and one way of linking to it.
(function () {
  const D = window.WPAB_DATA.build;
  const esc = t => String(t ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
  const by = (list, k = 'id') => Object.fromEntries(list.map(x => [x[k], x]));
  const ROUTE = { base: 'No MCP adapter installed', official: 'MCP adapter installed', third: 'Third-party MCP plugin installed (reference)' };
  // The first mention on a page links to the plugin itself.
  const ADAPTER = '<a href="https://wordpress.org/plugins/mcp-adapter/">WordPress’s MCP adapter plugin</a>';
  const CAUSE = { wordpress_lacks: 'WordPress has no way', connector_lacks: 'The MCP adapter has no way', plugin_lacks: 'A plugin has no way',
    didnt_ask: 'Didn’t ask the owner', stopped_early: 'Stopped short', did_it_wrong: 'Did something else', benchmark_fault: 'A fault in the benchmark' };
  const agents = by(D.agents), requests = by(D.requests), needs = by(D.needs), deadEnds = by(D.dead_ends), runs = by(D.runs);
  const short = q => q.prompt.split(/(?<=[.?!])\s/)[0];
  // A check that counts against the run: not done, required, and asked for.
  const failing = c => !c.passed && c.required !== false && c.status !== 'not_reached' && c.status !== 'not_judged';
  const base = document.body.dataset.base || '';
  const link = {
    run: r => `<a href="${base}run?id=${r.id}">${r.id}</a>`,
    request: q => `<a href="${base}request?id=${q.id}">${esc(short(q))}</a>`,
    agent: a => `<a href="${base}agent?id=${a.id}">${esc(a.name)}</a>`,
    deadEnd: id => deadEnds[id] ? `<a href="${base}deadend?id=${id}">${esc(deadEnds[id].title)}</a>` : esc(id),
  };
  // The ideas in the recommendations that would clear a dead end.
  const ideasFor = id => ((D.advice || {}).ideas || []).filter(x => (x.clears || []).includes(id));
  // A list of runs, each linked: the run, its agent, route and request, and its result.
  const runsTable = rs => `<div class="table-scroll"><table class="p-table"><thead><tr><th>Run</th><th>Agent</th><th>Setup</th><th>Prompt</th><th>Result</th></tr></thead><tbody>${
    rs.map(r => `<tr><td>${link.run(r)}</td><td>${link.agent(agents[r.agent])}</td><td>${esc(ROUTE[r.kind])}</td><td>${link.request(requests[r.request])}</td><td>${
      r.success_within ? 'Completed' : r.success ? 'Completed, with access it gave itself' : 'Not completed'}</td></tr>`).join('')}</tbody></table></div>`;
  const fact = (label, value, note) => value ? `<dt>${label}</dt><dd>${value}${note ? `<small>${note}</small>` : ''}</dd>` : '';
  const missing = (el, what, id) => { el.innerHTML = `<a class="go back" href="${base}runs">All runs</a><h1 class="title">We couldn’t find that ${what}</h1>
    <p class="lede">${id ? `There’s no ${what} “${esc(id)}”.` : `No ${what} was chosen.`}</p>`; };
  // Which prompts each idea is needed for: a prompt needs it when one of the abilities the MCP adapter lacked on that
  // prompt (the deeper read's write-ups) is one the idea would add. The same mapping as the story page's step chart.
  const CLEARS = {
    'core-write-abilities': /edit pages|create posts|site title|delete|front page|menus/i,
    'media-upload-ability': /upload images/i,
    'importer-ability': /create posts/i,
    'update-routes': /update/i,
    'plugin-write-abilities': /form/i,
    'install-plugin-ability': /install a plugin/i,
    'redirect-ability': /redirect/i,
  };
  const promptsNeeding = idea => CLEARS[idea] ? D.requests.filter(q => (D.write_ups || []).some(w => (w.requests || []).includes(q.id + '-official') && CLEARS[idea].test(w.title))) : [];
  // A run named by its trial (as the analysis quotes them), e.g. "dave-left-official__GL46yDX".
  const byTrial = by(D.runs, 'trial');
  window.REAL = { runsTable, fact, missing, D, esc, ROUTE, ADAPTER, CAUSE, agents, requests, needs, deadEnds, runs, short, failing, link, ideasFor, CLEARS, promptsNeeding, byTrial,
    done: rs => rs.filter(r => r.success_within).length, ours: D.runs.filter(r => r.kind === 'base' || r.kind === 'official') };
})();
