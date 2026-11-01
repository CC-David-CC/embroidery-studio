#!/usr/bin/env python3
"""Prepare an isolated browser-only StitchFoundry source candidate.

The commit is a source-review candidate, not a verified source match for the
currently packaged upstream binary. Run only on a disposable clean checkout.
"""
import argparse
import re
import subprocess
from pathlib import Path

COMMIT = 'e5a88e038d4281c925c94538c1a2d6262b83b83f'
BLOCKED = (
    'ui.designFromPrompt', 'ui.redrawImage', 'ui.askAboutEmbroidery',
    'ui.checkSewout', 'ui.reportSewout', 'ui.account',
    'embroidery.publishToMakerFoundry', 'embroidery.sendToStitchShop',
)

def replace_exact(text, old, new, count=1):
    found = text.count(old)
    if found != count:
        raise ValueError(f'Unexpected source pattern count: {found}, expected {count}: {old[:100]!r}')
    return text.replace(old, new)

def prepare(source, remove_open_link=False):
    source = Path(source).resolve()
    def git(*args):
        return subprocess.check_output(['git', '-C', str(source), *args], text=True).strip()
    if git('rev-parse', 'HEAD') != COMMIT or git('status', '--porcelain', '--untracked-files=normal'):
        raise ValueError('Expected a clean disposable checkout at the reviewed candidate commit')
    paths = {name: source / name for name in (
        'apps/vectorcraft-web/src/web.rs', 'crates/ui-egui/src/menus.rs',
        'crates/ui-egui/src/embroidery/panel.rs', 'crates/ui-egui/src/simple.rs',
        'crates/ui-egui/src/palette.rs',
    )}
    files = {name: path.read_text() for name, path in paths.items()}
    name = 'apps/vectorcraft-web/src/web.rs'
    text = files[name]
    text = replace_exact(text, '    let ai_ctx = ctx.clone();\n', '')
    text = replace_exact(text, '        // Design from Prompt and Ask About Embroidery: the browser\'s fetch, the key kept by it.\n        http_post_async: Some(http_post_async(ai_ctx)),\n        secrets: Some(Box::new(BrowserSecrets)),\n', '        // Codi browser desktop: external provider and account services are unavailable.\n')
    if remove_open_link:
        start_link = text.index('                        // Open in StitchFoundry: `?open=`')
        end_link = text.index('                        app\n', start_link)
        text = text[:start_link] + '                        // Third-party design links are unavailable in the browser desktop.\n' + text[end_link:]
    start = text.index('/// HTTPS POSTs (Design from Prompt, Ask About Embroidery)')
    end = text.index('/// Sample Color from Screen in the browser:', start)
    text = text[:start] + text[end:]
    files[name] = text
    name = 'crates/ui-egui/src/menus.rs'
    text = files[name]
    menu_items = (
        ('Ask About Embroidery…', 'ui.askAboutEmbroidery', 2),
        ('Check My Sew-out…', 'ui.checkSewout', 2),
        ('Foundry Account…', 'ui.account', 2),
        ('Design from Prompt…', 'ui.designFromPrompt', 1),
        ('Redraw Image with Claude…', 'ui.redrawImage', 1),
        ('Publish to MakerFoundry…', 'crate::embroidery::publish::COMMAND', 1),
        ('Send to StitchShop…', 'crate::embroidery::stitchshop::COMMAND', 1),
    )
    for label, command, count in menu_items:
        value = command if command.startswith('crate::') else f'"{command}"'
        pattern = re.compile(r'(?m)^(\s*)(c\(' + re.escape(f'"{label}", {value}') + r'\),)$')
        text, found = pattern.subn(r'\1#[cfg(not(target_arch = "wasm32"))]\n\1\2', text)
        if found != count:
            raise ValueError(f'Unexpected menu count for {label}: {found}, expected {count}')
    for command in BLOCKED:
        old = '    (\n        "' + command + '",\n'
        text = replace_exact(text, old, '    #[cfg(not(target_arch = "wasm32"))]\n' + old)
    matcher = ' | '.join('"' + name + '"' for name in BLOCKED)
    for signature, result in [
        ('pub fn run_ui_command(app: &mut VectorcraftApp, id: &str, p: &Value) -> Option<Result<Value, String>> {\n', 'return Some(Err("This service is not available in this desktop".into()));'),
        ('pub fn enabled(app: &VectorcraftApp, id: &str) -> bool {\n', 'return false;'),
    ]:
        guard = '    #[cfg(target_arch = "wasm32")]\n    if matches!(id, ' + matcher + ') {\n        ' + result + '\n    }\n'
        text = replace_exact(text, signature, signature + guard)
    files[name] = text
    name = 'crates/ui-egui/src/embroidery/panel.rs'
    old = '            if button(ui, tl!("Send to StitchShop")).clicked() {'
    files[name] = replace_exact(files[name], old, '            #[cfg(not(target_arch = "wasm32"))]\n' + old)
    name = 'crates/ui-egui/src/simple.rs'
    text = files[name]
    for command in ('ui.askAboutEmbroidery', 'ui.checkSewout', 'ui.account'):
        old = '        "' + command + '",\n'
        text = replace_exact(text, old, '        #[cfg(not(target_arch = "wasm32"))]\n' + old)
    files[name] = text
    name = 'crates/ui-egui/src/palette.rs'
    text = files[name]
    old = '    items\n}\n\n/// A palette label'
    guard = '    #[cfg(target_arch = "wasm32")]\n    items.retain(|(_, id, _)| !matches!(id.as_str(), ' + matcher + '));\n'
    files[name] = replace_exact(text, old, guard + old)
    for name, text in files.items():
        paths[name].write_text(text)
    print('Prepared local-only browser candidate at', COMMIT)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--remove-open-link', action='store_true', help='Prepare the next candidate without third-party startup imports')
    args = parser.parse_args()
    prepare(args.source, remove_open_link=args.remove_open_link)
