// Motion is presentation only: never mutates inspection facts or runtime decisions.
export const durations={instant:90,quick:160,standard:240,emphasis:420,hero:700};
export const easings={standard:'cubic-bezier(.2,0,0,1)',emphasized:'cubic-bezier(.2,.8,.2,1)',anticipate:'cubic-bezier(.4,-.15,.2,1)',overshoot:'cubic-bezier(.2,1.4,.4,1)'};
export const springs={snappy:{stiffness:360,damping:28},soft:{stiffness:170,damping:24},heavy:{stiffness:110,damping:21}};
const reduced=matchMedia('(prefers-reduced-motion:reduce)');
let manual=localStorage.getItem('bt.motion')||'full',automatic=0,average=16,last=0,samples=0,slow=0,lastStep=0,hero=null;
export function level(){if(manual==='off')return 'minimal';return ['full','calm','minimal'][Math.max(automatic,manual==='calm'||reduced.matches?1:0)];}
function apply(){document.documentElement.dataset.motion=level();document.dispatchEvent(new CustomEvent('motionchange',{detail:{level:level(),average}}));}
export function setMotion(value){manual=value;automatic=0;localStorage.setItem('bt.motion',value);apply();}
export function motionStatus(){return {manual,effective:level(),averageFrameMs:Math.round(average*10)/10,automaticStep:automatic};}
export function spring(update,from=0,to=1,preset='snappy'){
 if(level()==='minimal'){update(to);return ()=>{};}
 const {stiffness,damping}=springs[preset];let position=from,velocity=0,previous=performance.now(),id,stopped=false;
 function tick(now){const dt=Math.min(.032,(now-previous)/1000);previous=now;velocity+=(stiffness*(to-position)-damping*velocity)*dt;position+=velocity*dt;update(position);if(!stopped&&(Math.abs(to-position)>.001||Math.abs(velocity)>.005))id=requestAnimationFrame(tick);else update(to);}
 id=requestAnimationFrame(tick);return ()=>{stopped=true;cancelAnimationFrame(id);};
}
export function enter(elements){if(level()==='minimal')return;[...elements].slice(0,16).forEach((el,i)=>el.animate([{opacity:0,transform:'translateY(10px)'},{opacity:1,transform:'translateY(0)'}],{duration:240,delay:i*28,easing:easings.standard,fill:'backwards'}));}
export function heroMotion(el,keyframes,options={}){hero?.cancel();if(level()==='minimal')return;hero=el.animate(keyframes,{duration:700,easing:easings.emphasized,...options});return hero;}
export function transition(change){if(level()==='full'&&document.startViewTransition)return document.startViewTransition(change);change();}
export function themeReveal(change,x=innerWidth-80,y=40){
 if(!document.startViewTransition||level()!=='full'){change();return;}
 const vt=document.startViewTransition(change);vt.ready.then(()=>document.documentElement.animate({clipPath:['circle(0 at '+x+'px '+y+'px)','circle('+Math.hypot(innerWidth,innerHeight)+'px at '+x+'px '+y+'px)']},{duration:420,easing:easings.standard,pseudoElement:'::view-transition-new(root)'})).catch(()=>{});
}
function govern(now){
 if(last&&!document.hidden){const dt=now-last;if(dt<200){average=average*.96+dt*.04;samples++;slow=average>20?slow+1:0;if(samples>100&&slow>90&&now-lastStep>4000&&automatic<2){automatic++;lastStep=now;slow=0;apply();}}}
 last=now;requestAnimationFrame(govern);
}
reduced.addEventListener('change',apply);document.addEventListener('visibilitychange',()=>{last=0;});apply();requestAnimationFrame(govern);
