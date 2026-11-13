/* tema claro/escuro: segue o sistema; o botão na barra fixa a escolha (guardada neste navegador) */
(function(){try{var t=localStorage.getItem("nf-tema");if(t)document.documentElement.setAttribute("data-theme",t);}catch(e){}
  function botao(){var nav=document.querySelector(".nav");if(!nav||nav.querySelector(".tema"))return;
    var b=document.createElement("button");b.className="tema";b.title="Claro / escuro";b.setAttribute("aria-label","Trocar entre claro e escuro");
    var lua='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>',
        sol='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>';
    function escuro(){var t=document.documentElement.getAttribute("data-theme");return t?t==="dark":matchMedia("(prefers-color-scheme:dark)").matches;}
    function pinta(){b.innerHTML=escuro()?sol:lua;var m=document.querySelector('meta[name="theme-color"]');if(m)m.content=escuro()?"#0f0f0f":"#ffffff";}
    b.onclick=function(){var t=escuro()?"light":"dark";document.documentElement.setAttribute("data-theme",t);try{localStorage.setItem("nf-tema",t);}catch(e){}pinta();};
    nav.appendChild(b);pinta();}
  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",botao);else botao();})();
/* Interações compartilhadas: pílula que desliza, brilho que segue o mouse, entrada em sequência, números que contam */
window.UI=(function(){
  function pilula(box){if(!box)return;var on=box.querySelector(".on"),p=box.querySelector(".pil");
    if(!p){p=document.createElement("span");p.className="pil";box.insertBefore(p,box.firstChild);}
    box.classList.add("pr");if(!on){p.style.width="0";return;}p.style.left=on.offsetLeft+"px";p.style.width=on.offsetWidth+"px";}
  document.addEventListener("pointermove",function(e){var g=e.target.closest&&e.target.closest(".glow");if(!g)return;
    var r=g.getBoundingClientRect();g.style.setProperty("--x",(e.clientX-r.left)+"px");g.style.setProperty("--y",(e.clientY-r.top)+"px");},{passive:true});
  var io="IntersectionObserver" in window?new IntersectionObserver(function(es){es.forEach(function(en){if(en.isIntersecting){en.target.classList.add("vis");io.unobserve(en.target);}});},{rootMargin:"0px 0px -40px 0px"}):null;
  function revelar(nos){[].forEach.call(nos,function(n,i){n.style.transitionDelay=Math.min(i,10)*45+"ms";if(io)io.observe(n);else n.classList.add("vis");});}
  function contar(el,alvo,fmt){if(alvo==null||isNaN(alvo)){el.textContent=fmt(alvo);return;}
    var de=+(el.dataset.v||0),t0=performance.now(),d=900;el.dataset.v=alvo;
    if(matchMedia("(prefers-reduced-motion:reduce)").matches||de===alvo){el.textContent=fmt(alvo);return;}
    (function q(t){var k=Math.min(1,(t-t0)/d),e=1-Math.pow(1-k,3);el.textContent=fmt(Math.round(de+(alvo-de)*e));if(k<1)requestAnimationFrame(q);})(t0);}
  addEventListener("resize",function(){[].forEach.call(document.querySelectorAll(".tabs,.segm"),pilula);});
  addEventListener("load",function(){[].forEach.call(document.querySelectorAll(".tabs,.segm"),pilula);});
  if(document.fonts)document.fonts.ready.then(function(){[].forEach.call(document.querySelectorAll(".tabs,.segm"),pilula);});
  return{pilula:pilula,revelar:revelar,contar:contar};
})();
