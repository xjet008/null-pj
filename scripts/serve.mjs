import http from 'node:http';
import {createReadStream,statSync} from 'node:fs';
import {resolve,sep,extname} from 'node:path';
const root=resolve('dist'),port=Number(process.env.PORT||4176),types={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json','.gz':'application/gzip','.wgsl':'text/plain; charset=utf-8','.png':'image/png','.zip':'application/zip','.webm':'video/webm','.mp4':'video/mp4'};
const server=http.createServer((req,res)=>{try{let path=decodeURIComponent(new URL(req.url,'http://localhost').pathname);if(path==='/')path='/index.html';const file=resolve(root,'.'+path);if(!file.startsWith(root+sep)){res.writeHead(403);res.end('Forbidden');return;}const s=statSync(file);if(!s.isFile())throw Error('not file');res.writeHead(200,{'Content-Type':types[extname(file)]||'application/octet-stream','Content-Length':s.size,'Cache-Control':'no-cache'});if(req.method==='HEAD'){res.end();return;}createReadStream(file).pipe(res);}catch{res.writeHead(404);res.end('Not found');}});
server.listen(port,'127.0.0.1',()=>console.log('NULL GENESIS · http://127.0.0.1:'+port+'/ · PID '+process.pid));
process.on('SIGINT',()=>server.close(()=>process.exit(0)));
process.on('SIGTERM',()=>server.close(()=>process.exit(0)));