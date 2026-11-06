// Screenshots design prototypes (serve repo root on :8766). Example: node shoot-prototypes.js pull-sheet design/screenshots/pull-sheet home,results,car home,results car:dark,results:zoom
// usage: node shoot.js <dir> <outdir> screen[,screen..] [desk screens] 
const {chromium,devices}=require('playwright');
const [dir,out,phone,desk,extra]=process.argv.slice(2);
(async()=>{const b=await chromium.launch();
const ph=await b.newContext({...devices['iPhone 13']});
const dk=await b.newContext({viewport:{width:1280,height:860},deviceScaleFactor:1});
const run=async(ctx,s,name,q='')=>{const p=await ctx.newPage();const errs=[];p.on('pageerror',e=>errs.push(e.message));
 await p.goto(`http://localhost:8766/design/${dir}/?s=${s}&shot=1${q}`,{waitUntil:'networkidle'});await p.waitForTimeout(400);
 await p.screenshot({path:`${out}/${name}.png`}); if(errs.length)console.log(name,errs); await p.close();};
for(const s of phone.split(','))await run(ph,s,'phone-'+s);
if(desk)for(const s of desk.split(','))await run(dk,s,'desk-'+s);
if(extra){for(const e of extra.split(',')){const [s,k]=e.split(':');await run(ph,s,`phone-${s}-${k}`,k==='dark'?'&theme=dark':'&zoom=200');}}
await b.close();})();
