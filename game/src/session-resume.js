/* Restore the existing session before allowing automatic writes. No save migration. */
async function resumeWorldOrCreate(){
 const candidates=[], rejected=[];
 try {
  const raw=localStorage.getItem(SESSION_KEY);
  if(raw){try{candidates.push({entry:JSON.parse(raw),source:'browser'})}catch{rejected.push('browser')}}
 }catch{/* IndexedDB can still provide the existing world. */}
 const durable=await readSessionDB();
 if(durable)candidates.push({entry:durable,source:'database'});
 const valid=[];
 for(const candidate of candidates){
  try{parseSessionSnapshot(candidate.entry.snapshot);valid.push(candidate)}
  catch{rejected.push(candidate.source)}
 }
 valid.sort((a,b)=>(Number(b.entry.savedAt)||0)-(Number(a.entry.savedAt)||0));
 if(valid.length){
  const entry=valid[0].entry;
  // If restore fails, the startup error panel is shown; the original save is kept.
  G.restore(entry.snapshot);
  G.paused=entry.paused!==false;
  if(Number.isFinite(entry.speed)&&entry.speed>0&&entry.speed<=250)G.speed=entry.speed;
  Session.phase='ready';Session.revision=Number(entry.revision)||0;
  Session.lastRevision=Session.revision;Session.lastTime=G.time;
  Session.lastSavedAt=Number(entry.savedAt)||0;Session.lastEntryAt=Session.lastSavedAt;
  Session.lastAttempt=Date.now();Session.status='Saved';
  $('#session-loading')?.remove();updateSessionStatus();
  note('Resumed your saved world. Save slots and exported files were kept.');
  return true;
 }
 if(rejected.length){
  Session.phase='recovery';
  throw Error('The saved current world could not be read. Its original data has been kept; automatic saving is stopped. Load an exported backup in the original game or recover the browser save before continuing.');
 }
 G.opts.seed='';G.newWorld();Session.phase='ready';Session.revision++;
 Session.lastTime=-1;Session.lastRevision=-1;Session.lastAttempt=Date.now();
 $('#session-loading')?.remove();
 note('New world generated. Existing archive slots remain available.');
 return false;
}
