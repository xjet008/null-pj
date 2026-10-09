// Exercise the actual studio envelope methods with a known synthetic key.
import {Studio} from '../../dist/store-v45.js';
import {checkGenome,canonical} from '../../dist/engine.js';
const chunks=[];for await(const chunk of process.stdin)chunks.push(chunk);
const input=JSON.parse(Buffer.concat(chunks).toString('utf8')),studio=new Studio();
await studio.loadKey(new Blob([Uint8Array.from(input.key)]));
studio.regenerate=async genome=>{await checkGenome(genome);return {genome};};
const unlocked=await studio.unlock45(input.envelope);
if(canonical(unlocked.genome)!==canonical(input.genome)||unlocked.hiddenMessage!=='native synthetic message')throw Error('Native payload changed in Studio');
const browserEnvelope=await studio.encrypt45(input.genome,'browser synthetic message');
let rejected=0;
for(const forged of [{...input.envelope,fingerprint:'f'.repeat(64)},
                      {...input.envelope,version:3},
                      {...input.envelope,nonce:Buffer.alloc(11).toString('base64')},
                      {...input.envelope,aad:Buffer.from('bad').toString('base64')},
                      {...input.envelope,ciphertext:input.envelope.ciphertext.slice(0,-4)+'AAAA'}]){
 try{await studio.unlock45(forged);}catch{rejected++;}
}
if(rejected!==5)throw Error('Studio accepted a forged V4.5 envelope');
await studio.loadKey(new Blob([Uint8Array.from(input.key).reverse()]));
let wrongKeyRejected=false;try{await studio.unlock45(input.envelope);}catch{wrongKeyRejected=true;}
if(!wrongKeyRejected)throw Error('Studio accepted a wrong key');
console.log(JSON.stringify({fingerprint:unlocked.genome.fingerprint,browserEnvelope,rejected,wrongKeyRejected}));
