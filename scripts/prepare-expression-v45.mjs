import fs from 'node:fs/promises';
import {upgradeV45} from '../dist/fusion-v45.js';
import {seal} from '../dist/engine.js';
const registry=JSON.parse(await fs.readFile('dist/data/traits-v45.json','utf8')),input=JSON.parse(await fs.readFile('native/work/experiments-v45.json','utf8')),base=input.items[35].baseline;
const items=[];for(const t of registry.traits.filter(t=>t.id.startsWith('V45.')))items.push({id:t.id,category:t.category,genome:await seal(upgradeV45(base,registry,{seed:'v45-operative-trait-fixture',categories:{[t.category]:t.id},framing:'Full-Body',grid:80}))});
await fs.writeFile('native/work/expression-v45.json',JSON.stringify({items}));console.log('Prepared '+items.length+' operative trait fixtures');
