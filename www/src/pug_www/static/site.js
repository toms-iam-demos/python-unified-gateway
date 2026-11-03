/* Shared interaction logic. Content and navigation come from the Python profile. */
(()=>{
const header=document.querySelector('.site-header'),toggle=document.querySelector('#menu-toggle'),menus=[...header.querySelectorAll('details')];
const close=()=>{menus.forEach(m=>m.open=false);header.classList.remove('nav-open');toggle.setAttribute('aria-expanded','false')};
toggle.onclick=()=>{const open=header.classList.toggle('nav-open');toggle.setAttribute('aria-expanded',String(open))};
menus.forEach(menu=>menu.addEventListener('toggle',()=>{if(menu.open)menus.filter(m=>m!==menu).forEach(m=>m.open=false)}));
document.addEventListener('click',event=>{if(!event.target.closest('.site-header'))close()});
document.addEventListener('keydown',event=>{if(event.key==='Escape')close()});
const search=document.querySelector('#catalog-search');if(!search)return;
let category='';const cards=[...document.querySelectorAll('[data-entry]')],filters=[...document.querySelectorAll('[data-category-filter]')];
const filter=()=>{const query=search.value.toLocaleLowerCase();let count=0;cards.forEach(card=>{const visible=(!category||card.dataset.category===category)&&card.dataset.search.toLocaleLowerCase().includes(query);card.hidden=!visible;if(visible)count++});document.querySelector('#catalog-count').textContent=`${count} ${count===1?'example':'examples'}`;document.querySelector('#empty-results').hidden=count>0};
search.addEventListener('input',filter);filters.forEach(button=>button.onclick=()=>{category=button.dataset.categoryFilter;filters.forEach(b=>b.setAttribute('aria-pressed',String(b===button)));filter()});
})();
