/** Captura a interface real por CDP. Requer Chrome com porta 9223 e app em 8501. */
import fs from 'node:fs';
import path from 'node:path';
const root=process.cwd();
const out=path.join(root,process.env.CAPTURE_DIR||'outputs/video-production/fullhd');
fs.mkdirSync(out+'/frames',{recursive:true});
const tabs=await(await fetch('http://127.0.0.1:9223/json')).json();
const ws=new WebSocket(tabs.find(t=>t.type==='page'&&t.url.includes('8501')).webSocketDebuggerUrl);
await new Promise(r=>ws.onopen=r);
let id=0,recording=false,last=0;
const pending=new Map(),frames=[],scenes=[];
const clock=()=>Number(process.hrtime.bigint())/1e9;
const start=clock();
function call(method,params={}){return new Promise((resolve,reject)=>{const key=++id;pending.set(key,{resolve,reject});ws.send(JSON.stringify({id:key,method,params}))})}
ws.onmessage=e=>{
 const m=JSON.parse(e.data);
 if(m.id){const p=pending.get(m.id);pending.delete(m.id);m.error?p.reject(m.error):p.resolve(m.result);return}
 if(m.method==='Page.screencastFrame'){
  call('Page.screencastFrameAck',{sessionId:m.params.sessionId});
  const t=clock()-start;
  if(recording&&t-last>=1/15){last=t;const file=`frames/${String(frames.length).padStart(7,'0')}.jpg`;fs.writeFileSync(out+'/'+file,Buffer.from(m.params.data,'base64'));frames.push({file,time:t,source_timestamp:m.params.metadata.timestamp})}
 }
};
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
async function ev(expression){const r=await call('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value}
async function click(text){const ok=await ev(`(()=>{const e=[...document.querySelectorAll('button,label')].find(e=>e.innerText.trim()===${JSON.stringify(text)});if(!e)return false;e.scrollIntoView({block:'center'});e.click();return true})()`);if(!ok)throw Error('Control missing: '+text);await sleep(1500)}
async function select(label,text){
 await call('Input.dispatchKeyEvent',{type:'keyDown',key:'Escape',windowsVirtualKeyCode:27});
 await call('Input.dispatchKeyEvent',{type:'keyUp',key:'Escape',windowsVirtualKeyCode:27});
 const control=await ev(`(()=>{const e=document.querySelector('[role="combobox"][aria-label="${label}"]');e.scrollIntoView({block:'center'});const b=e.closest('[data-testid="stSelectbox"]').querySelector('button');const r=b.getBoundingClientRect();return{x:r.x+r.width/2,y:r.y+r.height/2}})()`);
 await call('Input.dispatchMouseEvent',{type:'mousePressed',button:'left',clickCount:1,...control});
 await call('Input.dispatchMouseEvent',{type:'mouseReleased',button:'left',clickCount:1,...control});
 await sleep(1000);
 const pos=await ev(`(()=>{let e=[...document.querySelectorAll('[role="option"]')].find(e=>e.textContent.includes(${JSON.stringify(text)}));if(!e)return null;let r=e.getBoundingClientRect();return{x:r.x+r.width/2,y:r.y+r.height/2}})()`);
 if(!pos)throw Error('Option missing: '+text);
 await call('Input.dispatchMouseEvent',{type:'mousePressed',button:'left',clickCount:1,...pos});await call('Input.dispatchMouseEvent',{type:'mouseReleased',button:'left',clickCount:1,...pos});await sleep(1500)
}
async function upload(file,index=0){const{root:d}=await call('DOM.getDocument');const{nodeIds}=await call('DOM.querySelectorAll',{nodeId:d.nodeId,selector:'input[type="file"]'});await call('DOM.setFileInputFiles',{nodeId:nodeIds[index],files:[file]});await sleep(1600)}
async function ready(){await sleep(2000);for(let i=0;i<90;i++){if(!await ev(`document.body.innerText.includes('Analisando')||[...document.querySelectorAll('button')].some(e=>e.innerText==='Stop')`))return;await sleep(1000)}throw Error('Processing timed out')}
async function show(selector){await ev(`document.querySelector(${JSON.stringify(selector)})?.scrollIntoView({block:'center',behavior:'smooth'})`);await sleep(1500)}
async function heading(text){await ev(`([...document.querySelectorAll('h1,h2,h3')].find(e=>e.textContent.includes(${JSON.stringify(text)})))?.scrollIntoView({block:'start',behavior:'smooth'})`);await sleep(1500)}
async function fill(label,text){const pos=await ev(`(()=>{let e=[...document.querySelectorAll('input')].find(e=>e.getAttribute('aria-label')===${JSON.stringify(label)});if(!e){let l=[...document.querySelectorAll('label')].find(e=>e.textContent.trim()===${JSON.stringify(label)});e=l&&document.getElementById(l.htmlFor)}if(!e)return null;e.scrollIntoView({block:'center'});e.focus();return true})()`);if(!pos)throw Error('Input missing: '+label);await call('Input.dispatchKeyEvent',{type:'keyDown',key:'a',code:'KeyA',modifiers:2,windowsVirtualKeyCode:65});await call('Input.insertText',{text});await call('Input.dispatchKeyEvent',{type:'keyDown',key:'Tab',windowsVirtualKeyCode:9});await sleep(700)}
async function scene(number,title,action){if(process.env.ONLY_SCENES&&!process.env.ONLY_SCENES.split(',').includes(String(number)))return;console.log('START',number,title);const item={number,title,start_seconds:clock()-start};scenes.push(item);try{await action();item.status='captured'}catch(e){item.status='failed';item.error=String(e);console.log(item.error)}item.end_seconds=clock()-start;fs.writeFileSync(out+'/scenes.json',JSON.stringify(scenes,null,2));console.log('END',number,item.status)}
await call('Page.enable');await call('Emulation.setDeviceMetricsOverride',{width:1920,height:1080,deviceScaleFactor:1,mobile:false});await call('Emulation.setEmulatedMedia',{features:[{name:'prefers-color-scheme',value:'dark'}]});
recording=true;await call('Page.startScreencast',{format:'jpeg',quality:85,maxWidth:1920,maxHeight:1080,everyNthFrame:1});
await scene(3,'Fisioterapia sem desvio',async()=>{await click('Vídeo');await select('Contexto','Elevação bilateral dos braços');await upload(root+'/outputs/rehab24-review/selected/01_ex2_correto.mp4');await click('Analisar vídeo');await ready();await show('video');await ev(`(()=>{let v=document.querySelector('video');if(v){v.muted=true;return v.play()}})()`);await sleep(9000);});
await scene(4,'Fisioterapia com assimetria',async()=>{await upload(root+'/outputs/rehab24-review/selected/02_ex2_assimetria.mp4');await click('Analisar vídeo');await ready();await show('video');await ev(`(()=>{let v=document.querySelector('video');if(v){v.muted=true;return v.play()}})()`);await sleep(12000);});
await scene(5,'Cadeira antes e depois',async()=>{await select('Contexto','Movimentação em leito/cadeira');for(const suffix of ['before','after']){await upload('/home/caio-lucas/Documentos/IA-PARA-DEVS/fase_4_base_de_dados/sit-to-stand/out_Subject_14_'+suffix+'.mp4');await click('Analisar vídeo');await ready();await show('video');await ev(`(()=>{let v=document.querySelector('video');if(v){v.muted=true;v.currentTime=${suffix==='after'?26:6};v.play()}})()`);await sleep(9000)}});
await scene(6,'SPIRA controle e paciente',async()=>{await click('Áudio');for(const name of ['01_controle_continuo.wav','02_paciente_pausas.wav']){await upload(root+'/outputs/spira-review/selected/'+name);await click('Analisar áudio');await ready();await heading('Transcrição');await sleep(4000);await ev(`document.querySelector('[data-testid="stMain"]')?.scrollBy({top:600,behavior:'smooth'})`);await sleep(4000)}});
await scene(7,'Sentimentos e negação',async()=>{for(const name of ['positivo.wav','negativo.wav','sintoma.wav','negacao.wav']){await upload('/home/caio-lucas/Documentos/IA-PARA-DEVS/audios-fase4/'+name);await click('Analisar áudio');await ready();await heading('Sentimento');await sleep(5000)}});
await scene(8,'Sinais persistentes e tendência',async()=>{await click('Sinais vitais');for(const name of ['development-vitals-2','development-vitals-3']){await select('Cenário',name);if(await ev(`document.querySelector('input[type="checkbox"]')?.checked`))await click('Reprodução acelerada (sem comprovação de cadência real)');await click('Reproduzir sessão');await sleep(23000);await heading('Alertas e evidências');await sleep(4000)}});
await scene(9,'Revisão de alerta',async()=>{const has=await ev(`document.body.innerText.includes('Responsável (demonstração)')`);if(has){await fill('Responsável (demonstração)','Caio Lucas Santos Silva');await fill('Comentário','Revisão de cenário sintético para demonstração acadêmica.');await click('Registrar');await sleep(2000);await select('Ação','Encerrar');await click('Registrar');await sleep(2000)}else{await click('Evidências e histórico');await sleep(6000)}});
await scene(10,'Prescrições e alertas',async()=>{await click('Histórico e fusão');await select('Cenário de prescrição','3 — mudança inesperada');await click('Processar cenário sintético');await ready();await heading('Evolução das prescrições');await sleep(6000);await heading('Alertas automáticos');await sleep(5000)});
await scene(11,'Integração explícita de eventos',async()=>{
 const latest=(dir,test)=>fs.readdirSync(dir).map(n=>path.join(dir,n,'report.json')).filter(p=>fs.existsSync(p)).map(p=>({p,d:JSON.parse(fs.readFileSync(p))})).filter(x=>test(x.d)).sort((a,b)=>b.d.started_at.localeCompare(a.d.started_at))[0]?.p;
 const files=[{file:latest(root+'/outputs/video',d=>d.events?.some(e=>e.event_type==='asymmetry')),time:'2026-01-01T00:00:10+00:00'},{file:latest(root+'/outputs/audio',d=>d.events?.some(e=>e.event_type==='long_pause_observed')),time:'2026-01-01T00:00:00+00:00'}];
 for(const item of files){if(!item.file)throw Error('Event report not found');await upload(item.file,1);await fill('Início da captura com fuso horário (ISO 8601)',item.time);await click('Integrar eventos de mídia');await ready();await heading('Linha do tempo de eventos');await sleep(5000)}await heading('Alertas automáticos');await sleep(5000);
});
recording=false;await call('Page.stopScreencast');
fs.writeFileSync(out+'/frames.json',JSON.stringify(frames));
for(const s of scenes){const selected=frames.filter(f=>f.time>=s.start_seconds&&f.time<=s.end_seconds);if(!selected.length)continue;let lines=[];for(let i=0;i<selected.length;i++){lines.push(`file '${selected[i].file}'`);lines.push(`duration ${Math.max(.001,(selected[i+1]?.time??s.end_seconds)-selected[i].time)}`)}lines.push(`file '${selected.at(-1).file}'`);fs.writeFileSync(out+`/scene-${String(s.number).padStart(2,'0')}.ffconcat`,lines.join('\n')+'\n')}
fs.writeFileSync(out+'/capture-manifest.json',JSON.stringify({viewport:[1920,1080],theme:'dark',method:'Chrome CDP screencast of actual application, variable source frames',audio:false,frames:frames.length,scenes},null,2));
ws.close();
