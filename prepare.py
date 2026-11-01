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
DIST_HASHES={
    'index.html':'681b68fbf8f37fe3531a5f522fba3d3fac00b69807fc936a1def72e0ce41666a',
    'vectorcraft-web-78d9970330c6ad52.js':'032acacb4f8ee9db8d3c2174d2f0edfe4b33f10551b73bfaf08179810356d5b3',
    'vectorcraft-web-78d9970330c6ad52_bg.wasm':'4599a7093dcb85cc2a8f0a3d4930629eb20524e1c948264af55b4011f5eaa92d',
}



def prepare(archive, local_dist, source_archive):
    source_archive=Path(source_archive)
    h=hashlib.sha256()
    with source_archive.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
    if h.hexdigest()!='4904901cb96755a4eb3bcd64b6898f9958c95c3d010ad28fec2efc385ad1b0ee':raise ValueError('Source archive hash mismatch')
    local_dist=Path(local_dist)
    if not local_dist.is_dir() or {p.name for p in local_dist.iterdir()} != set(DIST_HASHES):
        raise ValueError('Unexpected local build contents')
    for name,expected in DIST_HASHES.items():
        path=local_dist/name
        if path.is_symlink() or not path.is_file():raise ValueError('Invalid local build file: '+name)
        h=hashlib.sha256()
        with path.open('rb') as stream:
            for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
        if h.hexdigest()!=expected:raise ValueError('Local build hash mismatch: '+name)

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
            seen=set()
            for item in entries:
                if item.is_dir():continue
                if not item.filename.startswith(PREFIX):raise ValueError('Unexpected release path')
                relative=PurePosixPath(item.filename[len(PREFIX):])
                if relative.is_absolute() or not relative.parts or any(x in ('.','..') or not re.fullmatch(r'[A-Za-z0-9_+.-]+',x) for x in relative.parts):raise ValueError('Unsafe release path')
                if relative in seen:raise ValueError('Duplicate release path: '+item.filename)
                seen.add(relative)
                name=relative.name
                # Runtime code comes exclusively from the reviewed local build.
                if len(relative.parts)==1 and (name=='index.html' or re.fullmatch(r'vectorcraft-web-.*\.(?:js|wasm)',name)):continue
                if name in ('.htaccess','_headers'):continue
                if name in ('NOTICE','LICENSE-MIT','LICENSE-APACHE','LICENSE_FOXIT'):relative=relative.with_name(name+'.txt')
                elif name in ('README.md','HOSTING.md','ASSETS.md'):relative=relative.with_suffix('.txt')
                elif relative.suffix not in ('.html','.js','.wasm','.ttf','.txt'):raise ValueError('Unexpected release file: '+name)
                target=stage.joinpath(*relative.parts);target.parent.mkdir(parents=True,exist_ok=True)
                with bundle.open(item) as src,target.open('wb') as dst:shutil.copyfileobj(src,dst,1024*1024)
                assets.append('vendor/'+relative.as_posix())
        for required in ('NOTICE.txt','LICENSE-MIT.txt','LICENSE-APACHE.txt'):
            if not (stage/required).is_file():raise ValueError('Missing upstream notice: '+required)
        for name in DIST_HASHES:
            shutil.copyfile(local_dist/name,stage/name);assets.append('vendor/'+name)
        shutil.copyfile(source_archive,stage/'corresponding-source.zip');assets.append('vendor/corresponding-source.zip')
        shutil.copyfile(ROOT/'prepare.py',stage/'prepare.py.txt');assets.append('vendor/prepare.py.txt')
        (stage/'LOCAL_ONLY.txt').write_text('Browser build from StitchFoundry source e5a88e038d4281c925c94538c1a2d6262b83b83f, patched with prepare_local_source.py and prepare_file_bridge.py to disable provider features and route Open and Place through My files. WASM SHA-256: '+DIST_HASHES['vectorcraft-web-78d9970330c6ad52_bg.wasm']+'\nThe upstream release archive supplies notices and fonts, not executable code. This is not a verified source match for the earlier release binary.\n')
        assets.append('vendor/LOCAL_ONLY.txt')
        page=stage/'index.html';html=page.read_text();match=re.search(r'<script type="module">\s*(.*?)\s*</script>',html,re.S)
        if not match or html.count('<script type="module">')!=1:raise ValueError('Unexpected release startup script')
        (stage/'entry.mjs').write_text(match.group(1)+'\n');assets.append('vendor/entry.mjs')
        page_html=html[:match.start()]+'<script type="module" src="./entry.mjs"></script>'+html[match.end():]
        if page_html.count('<head>')!=1:raise ValueError('Unexpected release head')
        # The editor is local-only. Its WASM contains optional provider/account
        # integrations, so keep direct third-party connections blocked even if
        # the host page later adopts a broader connect policy.
        policy="<meta http-equiv=\"Content-Security-Policy\" content=\"connect-src 'self'; form-action 'none'; base-uri 'none'\">"
        page.write_text(page_html.replace('<head>','<head>\n  '+policy,1))
        font_licenses=sorted('licenses/epaint-default-fonts-0.36.2/'+name for name in ('UFL.txt','OFL.txt','Hack-Regular.txt','emoji-icon-font-mit-license.txt'))
        if any(not (ROOT/name).is_file() for name in font_licenses):raise ValueError('Missing bundled font license')
        dependency_notices='licenses/RUST_DEPENDENCY_NOTICES.txt'
        if hashlib.sha256((ROOT/dependency_notices).read_bytes()).hexdigest()!='ef95487f79c701aa06342e6c0b0ba0da91ad6d8cb029255c8bbb6686d9adb370':raise ValueError('Dependency notice hash mismatch')
        manifest={'assets':sorted(assets+font_licenses+[dependency_notices,'examples/heart.svg'])}
        (ROOT/'app.json').write_text(json.dumps(manifest,indent=2)+'\n')
        stage.rename(destination)
    return len(assets)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archive',type=Path,required=True);p.add_argument('--local-dist',type=Path,required=True);p.add_argument('--source-archive',type=Path,required=True);a=p.parse_args();print('Prepared',prepare(a.archive,a.local_dist,a.source_archive),'release files.')
