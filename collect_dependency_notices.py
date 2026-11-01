import argparse,collections,concurrent.futures,hashlib,json,pathlib,urllib.request
parser=argparse.ArgumentParser(description='Collect license and notice texts for the pinned browser dependency graph');parser.add_argument('--metadata',type=pathlib.Path,required=True);parser.add_argument('--output',type=pathlib.Path,required=True);args=parser.parse_args();j=json.loads(args.metadata.read_text());pkgs={x['id']:x for x in j['packages']};nodes={x['id']:x for x in j['resolve']['nodes']};todo=[i for i in pkgs if pkgs[i]['name']=='vectorcraft-web'];seen=set()
while todo:
 i=todo.pop()
 if i in seen:continue
 seen.add(i)
 for e in nodes[i]['deps']:
  if any(k['kind'] in (None,'build') for k in e['dep_kinds']):todo.append(e['pkg'])
repos={
'accesskit':('AccessKit/accesskit','a55d3e1a18bb9ef0e4bccc9083fb13c3e0ad8969',['LICENSE-APACHE','LICENSE-MIT','LICENSE.chromium']),
'alloc-stdlib':('dropbox/rust-alloc-no-stdlib','ae42d22078b98549e987d2f03d12df7b984fde47',['LICENSE']),
'egui':('emilk/egui','49682f8baa058bf49e011035cfbd6e825f88a5ef',['LICENSE-APACHE','LICENSE-MIT']),
'i_key_sort':('iShape-Rust/iKeySort','688424e09b7758d04e62e350160d164c7384f54b',['LICENSE']),
'i_overlay':('iShape-Rust/iOverlay','117637e3a65804973da2bfd7c59f42773f4dcc0d',['LICENSE-APACHE','LICENSE-MIT']),
'profiling':('aclysma/profiling','8271551172eb6fa4cba47369aedd93790c623df9',['LICENSE-APACHE','LICENSE-MIT']),
'spirv':('gfx-rs/rspirv','8afc3d0ac8e158128cd1410bb2e4b4c26ab11bb4',['LICENSE']),
'wasmi':('wasmi-labs/wasmi','2970aa871cc1001b57b267ccecdcd1e42306199e',['LICENSE-APACHE','LICENSE-MIT']),
'wasmparser':('bytecodealliance/wasm-tools','e66235859a6ec0502bf6f9dcc358953eda4cafcc',['LICENSE-APACHE','LICENSE-Apache-2.0_WITH_LLVM-exception','LICENSE-MIT'])}
egui={'ecolor','eframe','egui','egui-wgpu','egui_extras','egui_glow','emath','epaint','epaint_default_fonts'};wasmi={'wasmi','wasmi_collections','wasmi_core','wasmi_ir'}
def urls_for(q):
 name=q['name'];vcs=json.loads((pathlib.Path(q['manifest_path']).parent/'.cargo_vcs_info.json').read_text());rev=vcs['git']['sha1']
 if name in ('enum-map','enum-map-derive'):return [f'https://codeberg.org/xfix/enum-map/raw/commit/{rev}/LICENSES/{x}.txt' for x in ('Apache-2.0','MIT')]
 key='egui' if name in egui else 'wasmi' if name in wasmi else name
 repo,expected,files=repos[key];assert rev==expected,(name,rev,expected)
 return [f'https://raw.githubusercontent.com/{repo}/{rev}/{file}' for file in files]
def fetch(url):
 with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'CodiServer-license-review'}),timeout=45) as r:
  data=r.read(300001);assert 0<len(data)<=300000;return data.decode('utf-8')
work=[]
for i in sorted(seen,key=lambda x:(pkgs[x]['name'],pkgs[x]['version'])):
 q=pkgs[i];d=pathlib.Path(q['manifest_path']).parent
 files=sorted(x for x in d.iterdir() if x.is_file() and x.name.lower().startswith(('license','licence','copying','notice')))
 if not files and not (q.get('source') or '').startswith('registry+'):
  for parent in d.parents:
   if (parent/'.git').exists():
    files=sorted(x for x in parent.iterdir() if x.is_file() and x.name.lower().startswith(('license','licence','copying','notice')));break
 if files: work.append((q,[(f.name,lambda f=f:f.read_text(encoding='utf-8')) for f in files]))
 else:work.append((q,[(u,lambda u=u:fetch(u)) for u in urls_for(q)]))
urls=sorted({u for _,sources in work for u,_ in sources if u.startswith('https://')})
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
 results=list(pool.map(fetch,urls))
cache=dict(zip(urls,results));out=['Rust dependency notices for the StitchFoundry local browser candidate','Source: e5a88e038d4281c925c94538c1a2d6262b83b83f; Cargo.lock; wasm32 metadata.','This is a conservative normal/build dependency graph, not a claim all packages are linked.','Package licenses below are copied from the corresponding crate or exact upstream source revision.','']
for q,sources in work:
 out.extend(['='*72,f"{q['name']} {q['version']} | {q.get('license') or 'not declared'}",f"Repository: {q.get('repository') or 'workspace source'}",''])
 for source,reader in sources:
  text=cache[source] if source.startswith('https://') else reader();digest=hashlib.sha256(text.encode()).hexdigest();out.extend([f'--- {source} (SHA-256 {digest}) ---',text.rstrip(),''])
target=args.output;target.write_text('\n'.join(out)+'\n');print('packages',len(work),'remote files',len(urls),'bytes',target.stat().st_size,'sha256',hashlib.sha256(target.read_bytes()).hexdigest())
