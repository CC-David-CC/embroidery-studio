import './style.css';

export function mount(host){
  const {make,textButton}=host.ui,{mirrorFileContext,signedInSubject}=host.storage,owner=signedInSubject();host.w.ownerSub=owner;
  const body=make('div','window-content embroidery-studio'),bar=make('div','embroidery-bar'),status=make('div','app-status');
  const note=make('p','embroidery-note','In the editor, save or export your design, then choose it above and select Save to My files. Saved files sync with your account.');
  const select=document.createElement('select');select.setAttribute('aria-label','Editor saved file');
  const machineFormat=document.createElement('select');machineFormat.setAttribute('aria-label','Embroidery machine format');
  for(const format of ['dst','pes','jef','exp','vp3']){const option=make('option','',format.toUpperCase());option.value=format;machineFormat.append(option);}
  const machinePath=host.ui.appInput('Machine file path','/Embroidery.dst');
  const frame=document.createElement('iframe');frame.title='StitchFoundry embroidery editor';frame.sandbox='allow-scripts allow-same-origin allow-modals';
  frame.src=new URL('./vendor/index.html',import.meta.url).href;
  let disposed=false,api=null,timer=0,started=Date.now(),opened=null,versions=new Map(),lastList='';
  const valid=()=>!disposed&&!host.signal.aborted&&owner===signedInSubject();
  const tell=text=>{if(valid())status.textContent=text;};
  const open=textButton('Open from My files',async()=>{try{
    if(!api)throw Error('The editor is still starting.');
    const path=await host.storage.pickFile({extensions:['.stitchfoundry','.svg','.png','.jpg','.jpeg','.dst','.pes','.jef','.vp3','.exp'],signal:host.signal});
    if(!path||!valid())return;const context=await mirrorFileContext(),file=await context.files.read(path);if(!valid()||!context.valid())return;
    if(file.status==='conflict')throw Error('Resolve this file’s conflict in Files first.');
    if(!api.openFile(path.split('/').pop(),file.data))throw Error('The editor did not accept the file.');
    opened={path,name:path.split('/').pop(),version:file.version};versions.set(path,file.version);tell('Opening '+opened.name+' in the editor.');
  }catch(error){tell('Could not open file: '+error.message);}});
  const example=textButton('Open heart example',async()=>{try{
    if(!api)throw Error('The editor is still starting.');const response=await fetch(new URL('./examples/heart.svg',import.meta.url));if(!response.ok)throw Error('Example unavailable.');
    const bytes=new Uint8Array(await response.arrayBuffer());if(!valid())return;if(!api.openFile('heart.svg',bytes))throw Error('The editor did not accept the example.');
    opened=null;tell('Opened example artwork. Digitize it in the editor before exporting stitches.');
  }catch(error){tell('Could not open example: '+error.message);}});
  const save=textButton('Save to My files',async()=>{try{
    if(!api||!select.value)throw Error('Save or export in the editor, then choose the file above.');
    const name=select.value,raw=api.readFile(name);if(!ArrayBuffer.isView(raw)||raw.BYTES_PER_ELEMENT!==1||raw.byteLength>128*1024*1024)throw Error('Invalid or oversized editor file.');
    const context=await mirrorFileContext(),safe=context.name(name),path=opened?.name===safe?opened.path:'/'+safe;
    const saved=await context.files.write(path,Uint8Array.from(raw),versions.get(path)||null);if(!valid()||!context.valid())return;
    versions.set(path,saved.version);tell('Saved '+path+' on this device; syncing with the server.');
  }catch(error){tell('Could not save to My files: '+error.message);}});
  machineFormat.addEventListener('change',()=>{machinePath.value=machinePath.value.replace(/\.[a-z0-9]+$/i,'')+'.'+machineFormat.value;},{signal:host.signal});
  const exportMachine=textButton('Export stitches to My files',async()=>{try{
    if(!api)throw Error('The editor is still starting.');
    const context=await mirrorFileContext(),path=context.path(machinePath.value),format=machineFormat.value;
    if(!path.toLowerCase().endsWith('.'+format))throw Error('The file name must end in .'+format);
    tell('Exporting stitches…');const result=await api.execute('embroidery.export',{format});
    if(!valid()||!context.valid())return;
    if(typeof result?.dataBase64!=='string'||result.dataBase64.length>Math.ceil(128*1024*1024*4/3)+4)throw Error('The editor returned an invalid or oversized file.');
    const raw=atob(result.dataBase64),bytes=Uint8Array.from(raw,c=>c.charCodeAt(0));
    const saved=await context.files.write(path,bytes,versions.get(path)||null);if(!valid()||!context.valid())return;
    versions.set(path,saved.version);const warnings=Array.isArray(result.warnings)&&result.warnings.length?' Export notes: '+result.warnings.join('; '):'';tell('Saved '+path+' on this device; syncing with the server. Check the design before sewing.'+warnings);
  }catch(error){tell('Could not export stitches: '+error.message);}});
  function poll(){if(!valid())return;try{
    if(!api){api=frame.contentWindow?.vectorcraft;if(api?.captureDownloads){api.captureDownloads(true);open.disabled=false;example.disabled=false;save.disabled=false;tell('Editor ready. Saves and exports stay in this window until saved to My files.');}else{api=null;if(Date.now()-started>120000){tell('The editor did not start.');return;}}}
    if(api){const files=api.files();if(!Array.isArray(files)||files.length>16)throw Error('Unexpected editor file list.');const signature=JSON.stringify(files);if(signature!==lastList){lastList=signature;const selected=select.value;select.replaceChildren();for(const file of files){if(typeof file.path!=='string'||!Number.isSafeInteger(file.size))continue;const option=make('option','',file.path+' ('+file.size+' bytes)');option.value=file.path;select.append(option);}if([...select.options].some(option=>option.value===selected))select.value=selected;}}
  }catch(error){tell('Editor integration error: '+error.message);}timer=setTimeout(poll,1000);}
  open.disabled=true;example.disabled=true;save.disabled=true;bar.append(open,example,select,save,machineFormat,machinePath,exportMachine);body.append(bar,note,frame,status);tell('Loading StitchFoundry…');timer=setTimeout(poll,500);
  return {element:body,dispose(){disposed=true;clearTimeout(timer);frame.src='about:blank';frame.remove();}};
}
