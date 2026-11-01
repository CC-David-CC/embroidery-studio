#!/usr/bin/env python3
"""Archive the exact reviewed patched StitchFoundry tree, without build artifacts."""
import argparse
import hashlib
from pathlib import Path, PurePosixPath
import subprocess
import zipfile

COMMIT='e5a88e038d4281c925c94538c1a2d6262b83b83f'
PATCHED={
 'apps/vectorcraft-web/src/web.rs':'b6395eccff22fd9fd11e2715bc4f73f4d42b04b2998418efea81e2b9de073a04',
 'apps/vectorcraft-web/src/api.rs':'e54b286acffe1fc300925ffdccc4ac2b5cd9ec62e838c76d9e041dbfcdc43371',
 'crates/ui-egui/src/embroidery/viewer.rs':'79174e5d0586dbe4caa284d19cde5fd04b19ae5f18c0de40f2cdcef330970206',
 'crates/ui-egui/src/menus.rs':'43a3e86840fbfb37328a86e435e4432067fa07267e14f570ceef2f1ea0d6af1e',
 'crates/ui-egui/src/embroidery/panel.rs':'d59159c5621d33f800051566a27cc4f7c861bfb22f590ec00d041386cc56d879',
 'crates/ui-egui/src/simple.rs':'62cdd1abf27407fcc6a537ab5b084bdb29c9373efad3969973a46cb58fdc2ec3',
 'crates/ui-egui/src/palette.rs':'1fa162db088e373594dfe0d7e94e423256a41184fc4df8bbca5405f9414291ed',
}

def run(source,*args):return subprocess.check_output(['git','-C',str(source),*args])
def archive(source,host_source,output):
 source=Path(source).resolve();host_source=Path(host_source).resolve();output=Path(output)
 if run(source,'rev-parse','HEAD').decode().strip()!=COMMIT:raise ValueError('Unexpected source revision')
 status=run(source,'status','--porcelain=v1','--untracked-files=normal','-z').split(b'\0')
 changes={x[3:].decode() for x in status if x}
 if changes!=set(PATCHED) or any(x[:3]!=b' M ' for x in status if x):raise ValueError('Unexpected source changes')
 for name,digest in PATCHED.items():
  if hashlib.sha256((source/name).read_bytes()).hexdigest()!=digest:raise ValueError('Patched source mismatch: '+name)
 entries=run(source,'ls-files','--stage','-z').split(b'\0');files=[]
 for line in entries:
  if not line:continue
  meta,raw=line.split(b'\t',1);mode,_,stage=meta.split(b' ');name=raw.decode('utf-8');path=PurePosixPath(name)
  if mode not in (b'100644',b'100755') or stage!=b'0' or path.is_absolute() or '..' in path.parts:raise ValueError('Unexpected source entry: '+name)
  file=source.joinpath(*path.parts)
  if file.is_symlink() or not file.is_file():raise ValueError('Invalid source file: '+name)
  files.append((name,file,mode))
 if output.exists() or output.is_symlink():raise ValueError('Output already exists')
 host_files=('index.mjs','file-bridge.mjs','style.css','app.json','README.md','prepare_local_source.py','prepare_file_bridge.py','prepare_source_archive.py','collect_dependency_notices.py','examples/heart.svg','examples/stitched-rectangle.json')
 for name in host_files:
  f=host_source/name
  if f.is_symlink() or not f.is_file():raise ValueError('Missing host source: '+name)
 note=('Patched StitchFoundry browser source\nUpstream: https://github.com/Stitchwright/StitchFoundry/tree/'+COMMIT+'\nRevision: '+COMMIT+'\nThe modified files remove provider transport, account actions and MakerFoundry startup imports, and connect file actions to My files. See the host app source, prepare_local_source.py and prepare_file_bridge.py for the patches. Cargo.lock pins dependencies. Build instructions are in apps/vectorcraft-web/Trunk.toml and the host app README. This archive does not include generated assets or the dependency cache.\n').encode()
 with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  def put(name,data,mode):
   info=zipfile.ZipInfo(name,(1980,1,1,0,0,0));info.create_system=3;info.external_attr=(int(mode,8)<<16);info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,data,compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
  put('SOURCE-README.txt',note,b'100644')
  for name,file,mode in sorted(files):put('stitchfoundry/'+name,file.read_bytes(),mode)
  for name in host_files:put('desktop-integration/'+name,(host_source/name).read_bytes(),b'100644')
 print('Archived',len(files),'files; SHA-256',hashlib.sha256(output.read_bytes()).hexdigest())
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',required=True,type=Path);p.add_argument('--host-source',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args();archive(a.source,a.host_source,a.output)
