/* All API content is rendered with textContent; no untrusted HTML. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  let config, currentModel, busy = false;
  function node(tag, text, className) {
    const el = document.createElement(tag);
    if (text !== undefined) el.textContent = text;
    if (className) el.className = className;
    return el;
  }
  function projectLink(name) { return `https://github.com/${encodeURIComponent(config.username)}/${encodeURIComponent(name)}`; }
  function buildModel(repos) {
    const valid = repos.filter(r => !r.fork && !r.private && !r.archived && r.size > 0 && !config.exclude.includes(r.name));
    valid.sort((a,b) => (b.pushed_at || '').localeCompare(a.pushed_at || '') || b.name.localeCompare(a.name));
    const byName = new Map(valid.map(r => [r.name, r]));
    return {...config,
      featured: config.featured.filter(p => byName.has(p.repo)).map(p => ({...byName.get(p.repo), ...p, summary: byName.get(p.repo).description || p.summary})),
      recent: valid.slice(0, config.recent_limit)};
  }
  function render(model) {
    currentModel = model;
    document.querySelector('.intro').textContent = model.intro;
    $('keywords').replaceChildren(...model.keywords.map(k => node('span', k)));
    $('projects').replaceChildren(...model.featured.map((p,i) => {
      const card = node('a', undefined, 'project'); card.href = projectLink(p.name);
      const top = node('div', undefined, 'project-top');
      top.append(node('span', `0${i+1}`, 'project-number'), node('span', '↗', 'project-arrow'));
      const tags = node('div', undefined, 'tags'); tags.append(...p.tags.map(t => node('span',t)));
      card.append(top, node('p',p.category,'eyebrow'), node('h3',p.title), node('p',p.summary,'summary'), tags);
      return card;
    }));
    $('resource-links').replaceChildren(...model.resources.map(r => {
      const a = node('a'); a.href = r.url; a.append(node('span',r.label), node('span','↗')); return a;
    }));
    $('recent-projects').replaceChildren(...model.recent.map(r => {
      const a = node('a', undefined, 'recent-project'); a.href = projectLink(r.name);
      const top = node('div',undefined,'recent-top');
      const time = node('time',(r.pushed_at || '').slice(0,10)); if(r.pushed_at) time.dateTime = r.pushed_at;
      top.append(node('strong',r.name),time);
      const fallback = model.featured.find(p => p.name === r.name)?.summary || r.language || 'Research code';
      a.append(top, node('p',r.description || fallback)); return a;
    }));
  }
  async function fetchJSON(url) {
    const response = await fetch(url, {cache:'no-store', signal:AbortSignal.timeout(20000)});
    if(!response.ok) throw new Error(`GitHub HTTP ${response.status}`);
    return response.json();
  }
  async function refresh() {
    if(busy || !config) return;
    busy = true; $('refresh').disabled = true; $('status').textContent = 'Checking GitHub…';
    try {
      const repos = [];
      for(let page=1;page<=100;page++) {
        const batch = await fetchJSON(`https://api.github.com/users/${config.username}/repos?per_page=100&page=${page}`);
        if(!Array.isArray(batch)) throw new Error('Invalid GitHub response');
        repos.push(...batch);
        if(batch.length < 100) break;
        if(page === 100) throw new Error('Pagination limit exceeded');
      }
      render(buildModel(repos));
      $('status').textContent = `Live · checked ${new Date().toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'})}`;
    } catch(error) {
      $('status').textContent = currentModel ? 'Saved snapshot · live refresh unavailable' : 'Unable to load public projects';
      console.warn('Profile refresh unavailable:', error.message);
    } finally { busy = false; $('refresh').disabled = false; }
  }
  const dark = () => document.documentElement.dataset.theme === 'dark' || (!document.documentElement.dataset.theme && matchMedia('(prefers-color-scheme: dark)').matches);
  function updateThemeLabel() { $('theme').textContent = dark() ? 'Light mode ◐' : 'Dark mode ◐'; }
  $('theme').addEventListener('click', () => {document.documentElement.dataset.theme = dark() ? 'light' : 'dark'; updateThemeLabel();});
  $('refresh').addEventListener('click', refresh); updateThemeLabel();
  async function init() {
    try {
      config = await fetchJSON('profile.json');
      try { render(await fetchJSON('data/profile.json')); $('status').textContent = 'Saved snapshot · connecting…'; } catch(_) {}
    } catch(_) {
      // The embedded copy makes opening index.html directly from disk work too.
      config = window.PROFILE_CONFIG;
      if(window.PROFILE_INITIAL) { render(window.PROFILE_INITIAL); $('status').textContent = 'Saved snapshot · connecting…'; }
    }
    if(config) await refresh(); else $('status').textContent = 'Start a local server to preview this page';
  }
  setInterval(() => { if(!document.hidden) refresh(); }, 300000);
  document.addEventListener('visibilitychange', () => { if(!document.hidden) refresh(); });
  init();
})();
