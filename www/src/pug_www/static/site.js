/* Navigation and catalog facets are derived from the Python content registry. */
(()=>{
const header=document.querySelector('.site-header'),toggle=document.querySelector('#menu-toggle'),menus=[...header.querySelectorAll('details')];
const close=()=>{menus.forEach(menu=>menu.open=false);header.classList.remove('nav-open');toggle.setAttribute('aria-expanded','false')};
toggle.onclick=()=>{const open=header.classList.toggle('nav-open');toggle.setAttribute('aria-expanded',String(open))};
menus.forEach(menu=>menu.addEventListener('toggle',()=>{if(menu.open)menus.filter(other=>other!==menu).forEach(other=>other.open=false)}));
document.addEventListener('click',event=>{if(!event.target.closest('.site-header'))close()});
document.addEventListener('keydown',event=>{if(event.key==='Escape')close()});
const search=document.querySelector('#catalog-search');if(!search)return;
const cards=[...document.querySelectorAll('[data-entry]')],facets=[...document.querySelectorAll('[data-facet]')],groups=[...document.querySelectorAll('[data-process-group]')];
const filter=()=>{
 const query=search.value.toLocaleLowerCase();let count=0;
 cards.forEach(card=>{const visible=card.dataset.search.toLocaleLowerCase().includes(query)&&facets.every(select=>!select.value||(card.dataset[select.dataset.facet]||'').split('|').includes(select.value));card.hidden=!visible;if(visible)count++});
 groups.forEach(group=>{const visible=[...group.querySelectorAll('[data-entry]')].filter(card=>!card.hidden).length;group.hidden=visible===0;group.querySelector('.process-count').textContent=visible});
 document.querySelector('#catalog-count').textContent=`${count} ${count===1?'example':'examples'}`;document.querySelector('#empty-results').hidden=count>0;
};
search.addEventListener('input',filter);facets.forEach(select=>select.addEventListener('change',filter));
document.querySelector('#clear-facets').onclick=()=>{search.value='';facets.forEach(select=>select.value='');filter()};
})();

/* Invite drafts stay in this browser and never grant access or send mail. */
(()=>{
const form=document.querySelector('#invite-form');if(!form)return;
const choice=document.querySelector('#invite-example'),preview=document.querySelector('#invite-preview'),actions=document.querySelector('#invite-actions');let draft='';
form.addEventListener('submit',event=>{event.preventDefault();if(!form.reportValidity())return;const name=document.querySelector('#invite-name').value.trim(),email=document.querySelector('#invite-email').value.trim(),message=document.querySelector('#invite-message').value.trim(),title=choice.selectedOptions[0].textContent,url=new URL(choice.value,location.origin).href;
draft=`${name?'Hi '+name+',\n\n':''}Take a look at ${title}.\n\n${message?message+'\n\n':''}${url}\n\nThis link opens one example. Existing PUG access is required.`;
preview.textContent=draft;document.querySelector('#open-invite').href=url;document.querySelector('#email-invite').href='mailto:'+encodeURIComponent(email)+'?subject='+encodeURIComponent(title)+'&body='+encodeURIComponent(draft);actions.hidden=false;document.querySelector('#copy-result').textContent='';});
document.querySelector('#copy-invite').addEventListener('click',async()=>{const result=document.querySelector('#copy-result');try{await navigator.clipboard.writeText(draft);result.textContent='Copied.'}catch{result.textContent='Select and copy the preview text.'}});
form.addEventListener('input',()=>{actions.hidden=true;preview.textContent='Create a draft to preview your changes.'});
})();
(()=>{const search=document.querySelector('#app-search');if(!search)return;const cards=[...document.querySelectorAll('[data-app]')];search.addEventListener('input',()=>{let count=0;cards.forEach(card=>{card.hidden=!card.dataset.app.toLowerCase().includes(search.value.toLowerCase());if(!card.hidden)count++});document.querySelector('#app-count').textContent=`${count} apps and templates`})})();
