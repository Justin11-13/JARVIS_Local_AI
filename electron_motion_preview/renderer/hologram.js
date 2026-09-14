/* Original 3D holographic circuitry. Geometry is seeded; no movie assets. */
class HolographicCore {
 constructor(){
  this.motionTime=0;this.lastTime=null;this.speed=1;this.energy=1.58;this.speech=0;this.speechStart=0;this.previousState='idle';this.coreTime=0;this.layerPulses=[0,0,0];
  this.canvas=document.createElement('canvas');
  const gl=this.gl=this.canvas.getContext('webgl',{alpha:true,antialias:true,premultipliedAlpha:false,preserveDrawingBuffer:true});
  if(!gl)throw new Error('WebGL is unavailable');
  const vert=`precision highp float;
  attribute vec3 position; attribute vec3 detail;
  uniform float time,aspect,scale,density,activity,power,pointMode,waveTime;
  uniform vec3 shellPulse;
  uniform float coreTime;
  varying float brightness;varying float flavor;
  vec3 ry(vec3 p,float a){return vec3(cos(a)*p.x+sin(a)*p.z,p.y,-sin(a)*p.x+cos(a)*p.z);}
  vec3 rx(vec3 p,float a){return vec3(p.x,cos(a)*p.y-sin(a)*p.z,sin(a)*p.y+cos(a)*p.z);}
  vec3 rz(vec3 p,float a){return vec3(cos(a)*p.x-sin(a)*p.y,sin(a)*p.x+cos(a)*p.y,p.z);}
  void main(){
   float layer=detail.y;
   bool voiceTrace=layer>6.5&&layer<7.5;
   bool bridge=layer>7.5;
   float sourceLayer=layer;
   if(voiceTrace||bridge)layer=0.;
   vec3 p=position;
   if(layer<.5){
    // The outer shell, ribbon, particles AND anchored line endpoints share displacement.
    float radius=length(p);
    vec3 normal=normalize(p);
    float patch=sin(normal.x*5.1+normal.y*3.7+waveTime*2.1);
    float kick=pow(max(0.,patch),5.);
    float second=pow(max(0.,sin(normal.z*6.3-normal.y*4.2+waveTime*3.7)),7.);
    float displacement=activity*(.065*kick+.032*second);
    float attachment=smoothstep(.58,1.04,radius);
    p=normal*(radius+displacement*attachment);
   }
   float layerTime=layer>=3.?coreTime:time;
   float spin=layer<.5?.13:layer<1.5?.19:layer<2.5?.25:-.17;
   if(layer<2.5){
    // Spin in the band's local plane, THEN orient the whole layer.
    // Its normal stays fixed: points follow the visible ring instead of tumbling it.
    float tilt=layer<.5?.26:layer<1.5?1.18:-.72;
    float turn=layer<.5?.12:layer<1.5?-.08:.9;
    p=rz(rx(ry(p,layerTime*spin+layer*.68),tilt),turn);
   }else{
    p=rx(rz(p,layerTime*spin+layer*.31),.48+(layer-3.)*.24);
    p=ry(p,-.38);
   }
   if(bridge)p=mix(p,vec3(0.,0.,0.),detail.z);
   p=rx(p,.30);p=ry(p,.32);
   float distance=4.3-p.z;
   // Only one shell swells at a time, ordered inner -> middle -> outer.
   float pulse=layer<.5?shellPulse.x:layer<1.5?shellPulse.y:layer<2.5?shellPulse.z:0.;
   float speechScale=1.;
   gl_Position=vec4(p.x*scale/aspect*speechScale,p.y*scale*speechScale,0.,distance);
   float front=smoothstep(-1.05,.9,p.z);
   float shimmer=.94+.06*sin(layerTime*.85+position.x*24.+position.y*31.+layer);
   float sweep=pow(max(0.,sin(position.y*5.-layerTime*.65+layer*1.7)),18.);
   float longitude=atan(position.z,position.x);
   // Trail progression has the same angular sign as the geometry's motion.
   float traveling=pow(.5+.5*cos(longitude+layerTime*spin*.35),10.);
   brightness=detail.x*(.16+.84*front)*(shimmer+sweep*.12+pulse*(.10+traveling*.75))*power;
   if(layer<2.5){
    float irregular=sin(position.y*19.+waveTime*7.3)+.5*sin(longitude*17.-waveTime*11.7)+.3*sin(position.z*37.+waveTime*16.1);
    brightness*=1.+activity*.38*max(0.,irregular);
   }
   if(voiceTrace)brightness=detail.x*activity*(.28+.72*front)*(1.+.2*sin(longitude*23.+waveTime*8.))*power;
   if(bridge)brightness=detail.x*(.65+.35*front)*power;
   flavor=bridge?.7:detail.z;
   gl_PointSize=clamp((1.1+detail.z*1.8)*density*4.3/distance,1.,7.);
  }`;
  const frag=`precision mediump float;uniform float pointMode;uniform vec3 coreColorA;uniform vec3 coreColorB;varying float brightness;varying float flavor;
  void main(){float alpha=brightness;
   if(pointMode>.5){float d=length(gl_PointCoord-.5)*2.;alpha*=pow(max(0.,1.-d),1.1);}
   vec3 gold=mix(coreColorA,coreColorB,clamp(flavor*.55,0.,1.));
   gl_FragColor=vec4(gold,alpha);
  }`;
  const compile=(type,source)=>{const s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s;};
  this.program=gl.createProgram();gl.attachShader(this.program,compile(gl.VERTEX_SHADER,vert));gl.attachShader(this.program,compile(gl.FRAGMENT_SHADER,frag));gl.linkProgram(this.program);if(!gl.getProgramParameter(this.program,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(this.program));
  this.uniforms={};for(const name of ['time','aspect','scale','density','activity','power','pointMode','waveTime','shellPulse','coreTime','coreColorA','coreColorB'])this.uniforms[name]=gl.getUniformLocation(this.program,name);
  let seed=91923;const rnd=()=>{seed=(seed*1664525+1013904223)>>>0;return seed/4294967296;};
  const lines=[],points=[],triangles=[],shellAnchors=[];
  const push=(arr,p,b,l,f)=>arr.push(...p,b,l,f);
  const segment=(a,b,brightness,layer=0,flavor=.6)=>{push(lines,a,brightness,layer,flavor);push(lines,b,brightness,layer,flavor);};
  const sph=(u,v,r)=>[r*Math.cos(v)*Math.cos(u),r*Math.sin(v),r*Math.cos(v)*Math.sin(u)];
  const arc=(u,v,length,r,b,l)=>{let last=sph(u,v,r);for(let t=.018;t<=length+.018;t+=.018){const p=sph(u+Math.min(t,length),v,r);segment(last,p,b,l);last=p;}};
  // Broken horizontal circuitry: variable lengths, gaps, branch stubs, tiny panels.
  for(let layer=0;layer<3;layer++){
   const radius=[1.05,.82,.59][layer];
   for(let band=0;band<29;band++){
    const v=-1.30+band*.09;
    for(let n=0;n<17;n++){
     // Angular gaps leave readable, transparent windows through the shell.
     const gap=.48+.24*Math.sin(n*.9+band*.14+layer);
     if(rnd()<gap)continue;
     const u=n*Math.PI*2/17+rnd()*.065,len=.05+rnd()*.19,b=.28+rnd()*.58;
     arc(u,v,len,radius,b,layer);
     if(layer===0&&n%3===0&&band%3===0)shellAnchors.push({u,v});
     if(rnd()<.48){const dv=(rnd()>.5?1:-1)*(.025+rnd()*.06);segment(sph(u,v,radius),sph(u,v+dv,radius),b*.8,layer);arc(u,v+dv,len*.7,radius,b*.5,layer);}
     for(let dot=0;dot<28;dot++){const du=rnd()*len,dv=(rnd()-.5)*.035;push(points,sph(u+du,v+dv,radius+(rnd()-.5)*.012),.35+rnd()*.7,layer,rnd());}
     if(rnd()<.22){const dv=.012+rnd()*.022,p1=sph(u,v,radius),p2=sph(u+len*.4,v,radius),p3=sph(u+len*.4,v+dv,radius),p4=sph(u,v+dv,radius);for(const p of [p1,p2,p3,p1,p3,p4])push(triangles,p,.035+rnd()*.065,layer,.5);}
    }
   }
   // Long meridian fragments produce spherical curvature without a continuous grid.
   for(let n=0;n<9;n++){
    const u=n*Math.PI*2/9;let last=null;
    for(let j=0;j<95;j++){const v=-1.36+j*.029;if((j+n*7)%23>15){last=null;continue;}const p=sph(u,v,radius);if(last)segment(last,p,.36,layer);last=p;if(j%5===0)segment(p,sph(u+.015,v,radius),.65,layer);}
   }
  }
  // Dominant broken ribbons: clustered golden light, not a uniform wire globe.
  for(let belt=0;belt<3;belt++){
   const onBand=(u,offset=0)=>{
    // Great-circle guide is perpendicular to this layer's actual spin axis.
    const latitude=offset;
    return sph(u,latitude,[1.044,.814,.584][belt]);
   };
   for(let j=0;j<380;j++){
    const u=j*Math.PI*2/380;
    if(Math.sin(u*3.1+belt)<-.65)continue;
    const width=.007+.014*Math.pow(.5+.5*Math.sin(u*7+belt),3);
    for(let lane=-1;lane<=1;lane++)segment(onBand(u,lane*width*.45),onBand(u+.014,lane*width*.45),lane===0?.52:.20,belt,.9);
    const p1=onBand(u,-width),p2=onBand(u+.016,-width),p3=onBand(u+.016,width),p4=onBand(u,width);
    for(const p of [p1,p2,p3,p1,p3,p4])push(triangles,p,.09,belt,.8);
    for(let n=0;n<11;n++)push(points,onBand(u+rnd()*.016,(rnd()-.5)*width*4),.36+rnd()*.46,belt,.6+rnd()*.5);
    if(j%13===0){const a=onBand(u),b=a.map(v=>v*.72);segment(a,b,.22,belt,.5);}
    // Bright tapering markers share the exact band transform and reveal direction.
    if(j%95<12){const tail=(12-j%95)/12;push(points,onBand(u),.5+tail*.5,belt,1.+tail*.6);}
   }
  }
  // Tilted annular instruments inside the hollow volume.
  for(let layer=3;layer<7;layer++){
   const radius=.14+(layer-3)*.09;
   for(let k=0;k<180;k++){
    if((k+layer*7)%37>27)continue;
    const u=k*Math.PI*2/180,p=[Math.cos(u)*radius,Math.sin(u)*radius,0],q=[Math.cos(u+.028)*radius,Math.sin(u+.028)*radius,0];
    segment(p,q,.85,layer,1);
    if(k%3===0)segment(p,[p[0]*1.07,p[1]*1.07,.015],.65,layer,.9);
    for(let j=0;j<6;j++){const r=radius+(rnd()-.5)*.04;push(points,[Math.cos(u)*r,Math.sin(u)*r,(rnd()-.5)*.025],.5+rnd()*.4,layer,rnd());}
   }
  }
  // Every inward path begins at an existing outer-shell circuit endpoint.
  // It shares layer 0's transform, so the attachment cannot rotate off the shell.
  for(const {u,v} of shellAnchors){
   const a=sph(u,v,1.05),b=sph(u,v,.80),c=sph(u+.08,v*.86,.40+rnd()*.16);
   segment(a,b,.72,0,.9);segment(b,c,.60,0,.9);
   for(let j=0;j<9;j++){const q=j/8;push(points,a.map((value,k)=>value+(c[k]-value)*q),.52,0,.8);}
  }
  // A hollow, nested emitter; no solid central light bulb.
  // Irregular voice filaments lie ON the outer shell; radial size stays fixed.
  for(let band=0;band<11;band++){
   const v=-1.10+band*.21;let previous=null;
   for(let j=0;j<=280;j++){
    const u=j*Math.PI*2/280,p=sph(u,v+.008*Math.sin(u*17.+band),1.047);
    if(previous)segment(previous,p,.42,7,.9);previous=p;
   }
  }
  // Long anchored rays: shader joins moving outer endpoints to the stable hub.
  for(let k=0;k<Math.min(12,shellAnchors.length);k++){
   const {u,v}=shellAnchors[Math.floor(k*shellAnchors.length/Math.min(12,shellAnchors.length))];
   const p=sph(u,v,1.05);
   push(lines,p,.88,8,0);push(lines,p,.88,8,1);
   for(let j=0;j<22;j++)push(points,p,.75,8,j/21);
  }
  for(let j=0;j<7;j++)for(let i=0;i<100;i++){
   const u=i*Math.PI*2/100,r=.055+j*.012;
   segment([Math.cos(u)*r,Math.sin(u)*r,j*.006],[Math.cos(u+.05)*r,Math.sin(u+.05)*r,j*.006],.85,3,1.2);
  }
  this.batches=[{data:triangles,mode:gl.TRIANGLES,point:0},{data:lines,mode:gl.LINES,point:0},{data:points,mode:gl.POINTS,point:1}].map(b=>{const buffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buffer);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(b.data),gl.STATIC_DRAW);return{buffer,count:b.data.length/6,mode:b.mode,point:b.point};});
  this.position=gl.getAttribLocation(this.program,'position');this.detail=gl.getAttribLocation(this.program,'detail');
  this.palette={a:[1,.43,.018],b:[1,.75,.30]};
  this.vertices=lines.length/6+points.length/6;
 }
 setPalette(first,second){
  const valid=(value)=>Array.isArray(value)&&value.length===3&&value.every((part)=>Number.isFinite(part));
  if(valid(first))this.palette.a=first.map((part)=>Math.min(1,Math.max(0,part)));
  if(valid(second))this.palette.b=second.map((part)=>Math.min(1,Math.max(0,part)));
 }
 draw(ctx,w,h,t,state,quality){
  // Integrate speed continuously: switching states must never jump rotation angle.
  const dt=this.lastTime===null?0:Math.max(0,Math.min(.1,t-this.lastTime));this.lastTime=t;
  if(state!==this.previousState){if(state==='responding')this.speechStart=t;this.previousState=state;}
  // Synthetic speech: varied consonant attacks, vowel sustains and phrase silence.
  // This intentionally does not claim synchronization to real speech audio.
  const syllables=[[.14,.028,.16,.72],[.40,.02,.22,1],[.78,.035,.12,.43],[1.01,.023,.27,.88],[1.43,.04,.15,.55],[2.12,.025,.21,.94],[2.45,.019,.13,.56],[2.73,.04,.29,.79],[3.21,.022,.16,.48],[4.25,.028,.23,.86],[4.64,.018,.15,1],[4.92,.035,.18,.59],[5.27,.024,.32,.73]];
  const speechAt=(offset)=>{
   if(state!=='responding')return 0;
   const elapsed=t-this.speechStart-offset;if(elapsed<0)return 0;
   const phrase=elapsed%7.1;let value=0;
   for(const [onset,attack,release,amplitude] of syllables){
    const age=phrase-onset;if(age<0||age>attack+release)continue;
    const shape=age<attack?Math.sin(age/attack*Math.PI*.5):Math.pow(1-(age-attack)/release,1.7);
    value+=amplitude*shape;
   }return Math.min(1,value);
  };
  this.layerPulses=[speechAt(.09),speechAt(.045),speechAt(0)];
  const envelope=speechAt(0),responseRate=envelope>this.speech?32:12;
  this.speech+=(envelope-this.speech)*(1-Math.exp(-dt*responseRate));
  const ease=1-Math.exp(-dt*4),targetSpeed=(state==='thinking'||state==='responding')?2:state==='offline'?.18:1;
  this.speed+=(targetSpeed-this.speed)*ease;this.motionTime+=dt*this.speed;
  this.coreTime=this.motionTime;
  const targetEnergy=state==='offline'?.16:1.58;
  this.energy+=(targetEnergy-this.energy)*ease;
  // With frozen animation time, a selected state still receives its static appearance.
  const power=dt===0?targetEnergy:this.energy;
  const gl=this.gl,dpr=Math.min(devicePixelRatio||1,quality<1?1:1.5),cw=Math.max(1,Math.round(w*dpr)),ch=Math.max(1,Math.round(h*dpr));
  if(this.canvas.width!==cw||this.canvas.height!==ch){this.canvas.width=cw;this.canvas.height=ch;}
  gl.viewport(0,0,cw,ch);gl.clearColor(0,0,0,0);gl.clear(gl.COLOR_BUFFER_BIT);gl.useProgram(this.program);gl.disable(gl.DEPTH_TEST);gl.enable(gl.BLEND);gl.blendFunc(gl.SRC_ALPHA,gl.ONE);
  const u=this.uniforms;
  gl.uniform3fv(u.shellPulse,this.layerPulses);gl.uniform1f(u.coreTime,this.coreTime);
  gl.uniform3fv(u.coreColorA,this.palette.a);gl.uniform3fv(u.coreColorB,this.palette.b);
  const voice=state==='responding'?Math.pow(this.speech,.8)*1.35:0;
  gl.uniform1f(u.activity,voice);gl.uniform1f(u.waveTime,t-this.speechStart);
  gl.uniform1f(u.time,this.motionTime);gl.uniform1f(u.aspect,w/h);gl.uniform1f(u.scale,Math.min(2.65,(w/h)*2.5));gl.uniform1f(u.density,dpr);gl.uniform1f(u.power,power);
  for(const b of this.batches){gl.bindBuffer(gl.ARRAY_BUFFER,b.buffer);gl.enableVertexAttribArray(this.position);gl.vertexAttribPointer(this.position,3,gl.FLOAT,false,24,0);gl.enableVertexAttribArray(this.detail);gl.vertexAttribPointer(this.detail,3,gl.FLOAT,false,24,12);gl.uniform1f(u.pointMode,b.point);gl.drawArrays(b.mode,0,b.count);}
  ctx.clearRect(0,0,w,h);ctx.save();
  ctx.globalCompositeOperation='screen';
  if(quality>=1){ctx.filter='blur(7px)';ctx.globalAlpha=.40;ctx.drawImage(this.canvas,0,0,w,h);}
  ctx.filter='blur(1.5px)';ctx.globalAlpha=.6;ctx.drawImage(this.canvas,0,0,w,h);
  ctx.filter='none';ctx.globalAlpha=1;ctx.drawImage(this.canvas,0,0,w,h);ctx.restore();
 }
}
window.HolographicCore=HolographicCore;
