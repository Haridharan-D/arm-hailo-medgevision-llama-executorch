/** Local poster intro. Leaving always requires an explicit operator gesture. */
export function mountIntro(host,{classic=false,onEnter}){
 host.classList.add('poster-intro');host.classList.remove('leaving');host.hidden=false;
 host.setAttribute('role','dialog');host.setAttribute('aria-modal','true');host.setAttribute('aria-label','Medge Vision welcome — click anywhere or press Enter to begin');
 const poster=new URL('../assets/intro/medge-intro.png',import.meta.url).href;
 const buttonId=classic?'enter':'skip-boot';
 host.innerHTML='<div class="intro-capsule capsule-one" aria-hidden="true"></div><div class="intro-capsule capsule-two" aria-hidden="true"></div><div class="intro-art"><img class="intro-poster" src="'+poster+'" width="1672" height="941" alt="MEDGE SoC — Medical Edge Intelligence. AI-powered pharmaceutical quality inspection. Bharat AI-SoC Challenge 2026–27." decoding="async" fetchpriority="high"><div class="intro-scan" aria-hidden="true"></div><i class="intro-corner corner-tl" aria-hidden="true"></i><i class="intro-corner corner-tr" aria-hidden="true"></i><i class="intro-corner corner-bl" aria-hidden="true"></i><i class="intro-corner corner-br" aria-hidden="true"></i></div><div class="intro-footer"><div class="intro-runtime"><span class="intro-eyebrow">LOCAL INTELLIGENCE · TWO INDEPENDENT PIPELINES</span>'+(classic?'<p id="welcome-status">Connecting to the local inspection station…</p><div id="boot-list" hidden></div>':'<div id="boot-list" class="boot-list intro-boot-list" aria-label="Actual subsystem readiness"></div>')+'<span class="intro-hint">Click anywhere on this screen, or press Enter</span></div><button class="intro-enter" id="'+buttonId+'" type="button"><span>Enter inspection</span><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14m-6-6 6 6-6 6"/></svg></button></div><img id="splash-logo" hidden alt="">';
 host.addEventListener('click',()=>{if(!host.hidden&&!host.classList.contains('leaving'))onEnter();});
 host.querySelector('#'+buttonId).focus();
}
export function introExitDelay(){return matchMedia('(prefers-reduced-motion:reduce)').matches?0:320;}
