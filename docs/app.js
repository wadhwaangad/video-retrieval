let all=[], manifest, nextPage=1, activeFormat='';
const $ = selector => document.querySelector(selector);
const searchInput = $('#search'), formatSelect = $('#format'), summary = $('#summary');
const videos = $('#videos'), moreButton = $('#more'), cardTemplate = $('#card');
const esc=s=>s||"";
const link=id=>`https://www.youtube.com/watch?v=${id}`;
function pageCount(){return activeFormat ? manifest.format_pages[activeFormat] : manifest.pages}
function totalCount(){return activeFormat ? manifest.format_totals[activeFormat] : manifest.total}
function render(){const term=searchInput.value.toLowerCase(); const rows=all.filter(v=>`${v.title} ${v.channel_title} ${v.formats}`.toLowerCase().includes(term)); summary.textContent=`${totalCount().toLocaleString()} candidates · ${all.length.toLocaleString()} loaded · showing ${rows.length.toLocaleString()}`; videos.replaceChildren(...rows.map(v=>{const n=cardTemplate.content.cloneNode(true), a=n.querySelectorAll('a'); a.forEach(x=>x.href=link(v.video_id)); n.querySelector('img').src=v.thumbnail_url||`https://i.ytimg.com/vi/${v.video_id}/mqdefault.jpg`; n.querySelector('img').alt=esc(v.title); n.querySelector('small').textContent=v.formats||'unclassified candidate'; n.querySelector('h2 a').textContent=esc(v.title); n.querySelector('.channel').textContent=esc(v.channel_title); n.querySelector('.description').textContent=esc(v.description); return n})); moreButton.hidden=nextPage>pageCount();}
async function loadMore(){if(nextPage>pageCount())return; moreButton.disabled=true; const p=String(nextPage++).padStart(5,'0'); const base=activeFormat ? `data/formats/${activeFormat}` : 'data'; all.push(...await fetch(`${base}/page-${p}.json`).then(r=>r.json())); moreButton.disabled=false; render()}
async function changeFormat(){activeFormat=formatSelect.value; nextPage=1; all=[]; videos.replaceChildren(); await loadMore()}
fetch('manifest.json').then(r=>r.json()).then(async m=>{manifest=m; m.formats.forEach(x=>formatSelect.add(new Option(x,x))); await loadMore()}).catch(()=>summary.textContent='No exported manifest yet. Run the export command.'); searchInput.oninput=render; formatSelect.onchange=changeFormat; moreButton.onclick=loadMore;
