/* Keyboard and reading support only. No requests, provider actions or access changes. */
(()=>{
 'use strict';
 if(document.documentElement.dataset.pugHumanUi)return;
 document.documentElement.dataset.pugHumanUi='1';
 const main=document.querySelector('main');
 if(main&&!main.hasAttribute('tabindex'))main.tabIndex=-1;
 const rootToggle=document.querySelector('[data-human-nav]');
 rootToggle?.addEventListener('click',()=>{const header=rootToggle.closest('.catalog-header');const open=header.classList.toggle('nav-open');rootToggle.setAttribute('aria-expanded',String(open));});
 const menus=()=>[...document.querySelectorAll('.catalog-header details.resources-menu')];
 const closeMenus=except=>menus().forEach(menu=>{if(menu!==except)menu.open=false;});
 document.addEventListener('toggle',event=>{
   const menu=event.target;
   if(menu.matches?.('.catalog-header details.resources-menu')&&menu.open)closeMenus(menu);
 },true);
 document.addEventListener('keydown',event=>{
   if(event.key!=='Escape')return;
   const menu=event.target.closest?.('.catalog-header details.resources-menu[open]');
   if(menu){menu.open=false;menu.querySelector('summary')?.focus();event.preventDefault();return;}
   const header=event.target.closest?.('.catalog-header.nav-open');
   if(header){header.classList.remove('nav-open');const toggle=header.querySelector('.nav-toggle');toggle?.setAttribute('aria-expanded','false');toggle?.focus();event.preventDefault();}
 });
 document.addEventListener('click',event=>{
   if(!event.target.closest?.('.catalog-header details.resources-menu'))closeMenus();
   const anchor=event.target.closest?.('a[href^="#"]');
   if(!anchor||event.ctrlKey||event.metaKey||event.shiftKey||event.altKey)return;
   const id=anchor.getAttribute('href').slice(1);if(!id)return;
   requestAnimationFrame(()=>requestAnimationFrame(()=>{
     const target=document.getElementById(id);if(!target)return;
     if(!target.hasAttribute('tabindex'))target.tabIndex=-1;
     target.focus({preventScroll:true});
     target.scrollIntoView({block:'start',behavior:'auto'});
   }));
 });
 const sectionNav=document.querySelector('.workbench-nav-wrap');
 const offset=()=>document.documentElement.style.setProperty('--pug-anchor-offset',sectionNav?Math.ceil(sectionNav.getBoundingClientRect().height+24)+'px':'24px');
 offset();if(sectionNav&&typeof ResizeObserver==='function')new ResizeObserver(offset).observe(sectionNav);
 let pending=false;
 const title=()=>{
   pending=false;const heading=main?.querySelector('h1');
   const text=heading?.innerText.replace(/\s+/g,' ').trim();
   if(text&&text.length<=140)document.title=text+' | PUG';
 };
 const refresh=()=>{if(!pending){pending=true;requestAnimationFrame(title);}};
 if(main){new MutationObserver(refresh).observe(main,{childList:true,subtree:true});refresh();}
})();
