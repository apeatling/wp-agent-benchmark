// One recommendation: idea?id=core-write-abilities. The pitch in a reading column with a rail beside it (the prompts
// that need the idea, the dead ends it clears), then what we saw and the plan in order, then the ideas either side.
(function () {
  const R = window.REAL, { D, esc } = R, $p = document.getElementById('page');
  const ideas = (D.advice || {}).ideas || [];
  const id = new URLSearchParams(location.search).get('id') || '';
  const i = ideas.findIndex(x => x.id === id), x = ideas[i];
  if (!x) { R.missing($p, 'idea', id); $p.querySelector('.back').href = 'recommendations'; $p.querySelector('.back').textContent = 'All recommendations'; return; }
  document.title = `${x.title} · Building with WordPress · Agent Benchmarks`;

  const TRIAL = /\b([a-z0-9-]+-(?:official|none)__[A-Za-z0-9]+)\b/g;
  const runName = r => `${R.agents[r.agent].name}, ${R.ROUTE[r.kind]}`;
  const linkRuns = t => esc(t).replace(TRIAL, (m, tr) => R.byTrial[tr] ? `<a href="run?id=${R.byTrial[tr].id}">a run</a>` : m);
  // Agents wrote in markdown; the page shows their words plain.
  const plain = t => t.replace(/\*\*|`/g, '');
  const says = [], points = [];
  x.evidence.forEach(e => { const m = e.match(/^([a-z0-9-]+-(?:official|none)__[A-Za-z0-9]+):\s*"(.*)"$/s);
    if (m && R.byTrial[m[1]]) says.push({ r: R.byTrial[m[1]], q: plain(m[2]) }); else points.push(plain(e)); });
  const bold = t => t.replace(/(?<![\w$£€])(\d+ of (?:the )?\d+(?: [a-z]+)? runs?|\d+(?:\.\d+)?%)/g, '<b>$1</b>');

  // The prompts that need the idea; for ideas no single ability clears (a skill, an eval), the prompts its runs came from.
  const needs = R.promptsNeeding(x.id), seen = [...new Set(x.evidence.flatMap(e => [...e.matchAll(TRIAL)].map(m => R.byTrial[m[1]]?.request)))]
    .filter(Boolean).map(q => R.requests[q]).filter(Boolean);
  const need = needs.length ? needs : seen, needH = needs.length ? 'Prompts that need it' : 'Prompts where we saw it';
  const pitch = x.pitch || (window.IDEA_PITCH || {})[x.id] || [x.lead];
  const steps = [['Today', x.already], ['What to build', x.how], ['How it reaches agents', x.reaches], ['How we’ll know', x.know]]
    .filter(s => s[1]);
  const box = (h, body, cls = '') => body ? `<section class="${cls}"><h2>${h}</h2>${body}</section>` : '';
  const SHOW = 5;
  const prev = ideas[i - 1], next = ideas[i + 1];

  $p.innerHTML = `<a class="go back" href="recommendations">All recommendations</a>
    <h1 class="title">${esc(x.title)}</h1>
    <div class="idea-body">
      <div class="idea-main">
        <div class="idea-pitch">${pitch.map(t => `<p>${esc(t)}</p>`).join('')}</div>
        <section class="idea-part"><h2>What we saw</h2>
          ${points.length ? `<ul class="idea-pts">${points.map(e => `<li>${bold(linkRuns(e))}</li>`).join('')}</ul>` : ''}
          ${says.length ? `<ul class="idea-says">${says.map(s => `<li><blockquote>${esc(s.q)}</blockquote><cite>${esc(runName(s.r))}, <a href="run?id=${s.r.id}">run ${s.r.id}</a></cite></li>`).join('')}</ul>` : ''}
        </section>
        ${steps.length ? `<section class="idea-part"><h2>What it would take</h2>
          <ol class="idea-steps">${steps.map(([h, t]) => `<li><h3>${h}</h3><p>${esc(t)}</p></li>`).join('')}</ol></section>` : ''}
      </div>
      <aside class="idea-rail" aria-label="Act on this idea">
        ${box(needH, need.length && `<ul>${need.map((q, k) => `<li${k >= SHOW ? ' class="more-item"' : ''}>${R.link.request(q)}</li>`).join('')}</ul>
          ${need.length > SHOW ? `<button class="toggle" type="button" aria-expanded="false">Show all ${need.length} prompts ▼</button>` : ''}`)}
        ${box('Dead ends it clears', x.clears.length && `<ul>${x.clears.map(d => `<li>${R.link.deadEnd(d)}</li>`).join('')}</ul>`)}
      </aside>
    </div>
    <nav class="idea-nav" aria-label="Other ideas">
      <div>${prev ? `<a href="idea?id=${prev.id}"><small>Previous idea</small><span>${esc(prev.title)}</span></a>` : ''}</div>
      <div class="next">${next ? `<a href="idea?id=${next.id}"><small>Next idea</small><span>${esc(next.title)}</span></a>` : ''}</div>
    </nav>`;
  const t = $p.querySelector('.idea-rail .toggle');
  if (t) t.onclick = () => { const ul = t.previousElementSibling, open = ul.classList.toggle('open');
    t.setAttribute('aria-expanded', open); t.textContent = open ? 'Show fewer ▲' : `Show all ${need.length} prompts ▼`; };
})();
