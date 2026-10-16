// One prompt: the prompt as the title, how every run of it went at a glance, each run with what stopped it, and each
// check run by run, with the prompt's details (need, site, dead ends) in a rail beside it.
(function () {
  const R = window.REAL, { D, esc } = R, C = window.CHOOSE, $p = document.getElementById('page');
  const id = new URLSearchParams(location.search).get('id') || '', q = R.requests[id];
  if (!q) return R.missing($p, 'prompt', id);
  document.title = `${R.short(q)} · Building with WordPress · Agent Benchmarks`;
  const UNPLUG = '<span class="glyph" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="m19 5 3-3M2 22l3-3M6.3 20.3a2.4 2.4 0 0 0 3.4 0L12 18l-6-6-2.3 2.3a2.4 2.4 0 0 0 0 3.4ZM7.5 13.5 10 11M10.5 16.5 13 14M12 6l6 6 2.3-2.3a2.4 2.4 0 0 0 0-3.4l-2.6-2.6a2.4 2.4 0 0 0-3.4 0Z"/></svg></span>';
  const PLUG = '<span class="glyph" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22v-5M9 8V2M15 8V2M18 8v5a4 4 0 0 1-4 4h-4a4 4 0 0 1-4-4V8Z"/></svg></span>';
  const SETUPS = [['base', 'No MCP adapter installed', UNPLUG], ['official', 'MCP adapter installed', PLUG]];
  // The site each prompt runs on, in plain words (as on the Prompts page).
  const SITES = { bakery: 'A bakery’s site with a small online shop', plumber: 'A plumber’s site built with a page builder',
    club: 'A sailing club’s site with years of news', fresh: 'A brand-new WordPress site with nothing on it yet' };
  const EXISTING = new Set(['online-cafe-menu', 'online-booking', 'online-candle-shop', 'move-about-faq', 'move-blog-posts', 'move-off-wix']);
  const site = q.fixture === 'fresh' && EXISTING.has(q.id) ? 'A new WordPress site with a few pages the owner added' : SITES[q.fixture] || q.fixture;

  const rs = R.ours.filter(r => r.request === id);
  const RD = k => `<span class="rd ${k}" aria-hidden="true"></span>`;
  const state = r => r.success_within ? 'on' : 'no';
  const runsIn = k => D.agents.map(a => rs.find(r => r.kind === k && r.agent === a.id)).filter(Boolean);
  const say = r => `${R.agents[r.agent].name}, ${R.ROUTE[r.kind].toLowerCase()}: ${r.success_within ? 'completed' : 'not completed'}`;
  const why = r => { const c = Object.values(r.checks).find(c => R.failing(c) && (c.what_stopped || c.detail));
    return r.success_within ? '' : r.success ? 'Done only by going around the setup it was given.' : c ? c.what_stopped || c.detail : ''; };

  const strip = SETUPS.map(([k, l, ic]) => { const x = runsIn(k); return x.length ? `<div class="rq-set"><h2>${ic}${l}</h2><ul>${x.map(r =>
    `<li><a href="run?id=${r.id}" title="${esc(say(r))}">${RD(state(r))}<span>${esc(R.agents[r.agent].name)}</span></a></li>`).join('')}</ul></div>` : ''; }).join('');
  const runs = SETUPS.flatMap(([k]) => runsIn(k)).map(r => `<li><a href="run?id=${r.id}">${RD(state(r))}<span>
    <span class="who">${C.logo({ id: R.agents[r.agent].logo }, 14)}${esc(R.agents[r.agent].name)} <span class="where">· ${esc(R.ROUTE[r.kind])}</span></span>
    ${why(r) ? `<span class="why">${esc(why(r))}</span>` : ''}</span><span class="id">${esc(r.id)}</span></a></li>`).join('');
  const sets = SETUPS.filter(([k]) => runsIn(k).length);
  const checks = q.checks.map(c => `<tr><td>${esc(c.name)}${c.guard ? '<small>Checked on every prompt</small>' : ''}</td>${sets.map(([k]) =>
    `<td class="set">${runsIn(k).map(r => { const x = r.checks[c.id]; const s = !x || x.status === 'not_reached' ? 'skip' : x.passed ? 'on' : 'no';
      return `<span class="rd ${s}" title="${esc(R.agents[r.agent].name)}: ${s === 'on' ? 'passed' : s === 'no' ? 'failed' : 'not asked'}"></span>`; }).join('')}</td>`).join('')}</tr>`).join('');
  const ends = {}; rs.forEach(r => Object.values(r.checks).filter(R.failing).forEach(c => (c.dead_ends || []).forEach(d => { if (R.deadEnds[d]) (ends[d] ||= new Set()).add(r.id); })));
  const row = (dt, dd) => dd ? `<div><dt>${dt}</dt><dd>${dd}</dd></div>` : '';

  $p.innerHTML = `<a class="go back" href="prompts#${q.need}">All prompts</a>
    <h1>“${esc(q.prompt)}”</h1>
    ${q.follow_up ? `<p class="rn-fu"><b>Once it’s done</b>“${esc(q.follow_up)}”</p>` : ''}
    <div class="rq-strip">${strip}</div>
    <div class="rn-body">
      <div class="rn-main">
        <section><h2>Every run</h2><ul class="rq-runs">${runs}</ul></section>
        <section><h2>The checks</h2><table class="rq-checks"><thead><tr><th>Check</th>${sets.map(([, l]) => `<th class="set">${esc(l)}</th>`).join('')}</tr></thead><tbody>${checks}</tbody></table></section>
      </div>
      <aside class="rn-rail" aria-label="About this prompt"><dl>
        ${row('Need', `<a href="prompts#${q.need}">${esc(R.needs[q.need].name)}</a>`)}
        ${row('Site', esc(site))}
        ${row('Dead ends', Object.keys(ends).length && `<ul>${Object.keys(ends).map(d => `<li>${R.link.deadEnd(d)}</li>`).join('')}</ul>`)}
      </dl></aside>
    </div>`;
})();
