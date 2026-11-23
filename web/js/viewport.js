/** Pure viewport math: never lets the image drift beyond its own visible bounds. */
export function fitScale(vw,vh,iw,ih){return Math.min(vw/iw,vh/ih);}
export function constrain(x,y,scale,vw,vh,iw,ih){
 const w=iw*scale,h=ih*scale;
 return {x:w<=vw?(vw-w)/2:Math.max(vw-w,Math.min(0,x)),y:h<=vh?(vh-h)/2:Math.max(vh-h,Math.min(0,y))};
}
export function anchoredZoom(x,y,scale,next,cx,cy){const ratio=next/scale;return {x:cx-(cx-x)*ratio,y:cy-(cy-y)*ratio};}
