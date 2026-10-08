// Uses the actual Studio encryption methods with a synthetic key. No UI or files.
import {Studio} from '../../dist/store.js';
import {checkGenome,canonical} from '../../dist/engine.js';
const chunks=[];for await(const chunk of process.stdin)chunks.push(chunk);
const input=JSON.parse(Buffer.concat(chunks).toString('utf8'));
const studio=new Studio();studio.v3Catalog=[];
await studio.loadKey(new Blob([Uint8Array.from(input.key)]));
studio.regenerate=async genome=>{await checkGenome(genome);return {genome};};
const unlocked=await studio.unlockV3(input.envelope);
if(canonical(unlocked.genome)!==canonical(input.genome))throw Error('Python DNA changed after Studio unlock');
if(unlocked.hiddenMessage!=='synthetic hidden message')throw Error('Studio did not retain the encrypted hidden message');
const browserEnvelope=await studio.encryptV3(input.genome,'browser synthetic message');
let forgedRejected=false;try{await studio.unlockV3({...input.envelope,fingerprint:'f'.repeat(64)});}catch{forgedRejected=true;}
if(!forgedRejected)throw Error('Studio accepted a forged V3 identity');
console.log(JSON.stringify({unlockedFingerprint:unlocked.genome.fingerprint,browserEnvelope,forgedRejected}));
