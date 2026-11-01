/** Bridge the editor's browser file requests to the account's My files picker. */
export function createFileBridge({host,getApi,valid,getRevision,mark,tell,isBusy,setBusy,open}){
 let disposed=false,unbind=()=>{};
 const alive=()=>!disposed&&valid();
 async function place(){
  if(!alive()||isBusy())return;
  const revision=getRevision();setBusy(true);
  try{
   const api=getApi();if(typeof api?.placeFile!=='function')throw Error('Place from My files is unavailable in this editor build.');
   const selected=await host.storage.pickFile({signal:host.signal});if(!selected||!alive())return;
   const c=await host.storage.mirrorFileContext(),path=c.path(selected),file=await c.files.read(path);
   if(!alive()||!c.valid())return;
   if(file.status==='conflict')throw Error('Resolve the file conflict in Files first.');
   if(file.data.byteLength>128*1024*1024)throw Error('File exceeds 128 MiB.');
   if(getApi()!==api||getRevision()!==revision)throw Error('The editor changed while choosing the file; try again.');
   if(!api.placeFile(path.split('/').pop(),file.data))throw Error('The editor did not accept the file.');
   mark();tell('File ready to place from My files. Follow the editor’s placement controls.');
  }catch(e){if(alive())tell('Could not place file: '+e.message)}finally{setBusy(false)}
 }
 function bind(win){
  unbind();if(!win||disposed)return;
  const onOpen=()=>{if(alive())void open()},onPlace=()=>{if(alive())void place()};
  win.addEventListener('codi-open-my-files',onOpen);win.addEventListener('codi-place-my-files',onPlace);
  unbind=()=>{win.removeEventListener('codi-open-my-files',onOpen);win.removeEventListener('codi-place-my-files',onPlace)};
 }
 return {bind,place,dispose(){if(disposed)return;disposed=true;unbind();unbind=()=>{}}};
}
