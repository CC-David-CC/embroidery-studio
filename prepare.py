#!/usr/bin/env python3
"""Prepare the pinned StitchFoundry browser release for the app builder."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import tempfile
import zipfile

ROOT=Path(__file__).resolve().parent
ARCHIVE_SHA='ebcba487093c414e57d634beff032ad60b300c8296f8fbaf44993920ff60c6c6'
PREFIX='stitchfoundry-web-0.14.0/'


def prepare(archive):
    archive=Path(archive);h=hashlib.sha256()
    with archive.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
    if h.hexdigest()!=ARCHIVE_SHA:raise ValueError('StitchFoundry release archive hash mismatch')
    destination=ROOT/'vendor'
    if destination.exists() or destination.is_symlink():raise ValueError('Remove the previous prepared vendor directory first')
    with tempfile.TemporaryDirectory(prefix='.stitchfoundry-',dir=ROOT) as temp:
        stage=Path(temp)/'vendor';stage.mkdir();assets=[]
        with zipfile.ZipFile(archive) as bundle:
            entries=bundle.infolist()
            if len(entries)>256 or sum(x.file_size for x in entries)>200*1024*1024:raise ValueError('Unexpected release archive size')
            for item in entries:
                if item.is_dir():continue
                if not item.filename.startswith(PREFIX):raise ValueError('Unexpected release path')
                relative=PurePosixPath(item.filename[len(PREFIX):])
                if relative.is_absolute() or not relative.parts or any(x in ('.','..') or not re.fullmatch(r'[A-Za-z0-9_+.-]+',x) for x in relative.parts):raise ValueError('Unsafe release path')
                name=relative.name
                if name in ('.htaccess','_headers'):continue
                if name in ('NOTICE','LICENSE-MIT','LICENSE-APACHE','LICENSE_FOXIT'):relative=relative.with_name(name+'.txt')
                elif name in ('README.md','HOSTING.md','ASSETS.md'):relative=relative.with_suffix('.txt')
                elif relative.suffix not in ('.html','.js','.wasm','.ttf','.txt'):raise ValueError('Unexpected release file: '+name)
                target=stage.joinpath(*relative.parts);target.parent.mkdir(parents=True,exist_ok=True)
                with bundle.open(item) as src,target.open('wb') as dst:shutil.copyfileobj(src,dst,1024*1024)
                assets.append('vendor/'+relative.as_posix())
        page=stage/'index.html';html=page.read_text();match=re.search(r'<script type="module">\s*(.*?)\s*</script>',html,re.S)
        if not match or html.count('<script type="module">')!=1:raise ValueError('Unexpected release startup script')
        (stage/'entry.mjs').write_text(match.group(1)+'\n');assets.append('vendor/entry.mjs')
        page.write_text(html[:match.start()]+'<script type="module" src="./entry.mjs"></script>'+html[match.end():])
        manifest={'assets':sorted(assets+['examples/heart.svg'])}
        (ROOT/'app.json').write_text(json.dumps(manifest,indent=2)+'\n')
        stage.rename(destination)
    return len(assets)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archive',type=Path,required=True);a=p.parse_args();print('Prepared',prepare(a.archive),'release files.')
