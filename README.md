# Embroidery Studio

This app packages a locally rebuilt StitchFoundry 0.14.0 development browser build
(MIT OR Apache-2.0). The upstream web archive SHA-256 is
`ebcba487093c414e57d634beff032ad60b300c8296f8fbaf44993920ff60c6c6`.
The exact source commit for the older upstream archive's WebAssembly has not been established. Earlier
notes associated it with `e3b80b2ce3f5a3e9cabd00a4d4824b65dc35a017`, but the
binary contains account and Ask About Embroidery source paths absent from that
commit. Upstream commit `e5a88e038d4281c925c94538c1a2d6262b83b83f` predates
the archive timestamp and its README, notices, assets list and licenses match
the archive. It is a candidate for source review, not a verified build match.
Its upstream notices and font licenses are included in the packaged assets.
The upstream project describes the build as pre-release and reports software
round trips but no physical-machine sew-out yet; test on fabric before relying
on an export. Individual format behavior must be verified independently.

The earlier `0.14.0-rc.1` browser build panicked in Rust's system-time
implementation. The pinned newer development build avoids that observed panic
in the tested workflows; it is still pre-release software.

The live local-only browser build is built from source commit
`e5a88e038d4281c925c94538c1a2d6262b83b83f`, patched with
`prepare_local_source.py` and `prepare_file_bridge.py` in a clean checkout. Build the browser target using
its locked dependencies and Trunk release build, then supply its three output
files via `--local-dist`. The separately pinned upstream archive supplies fonts
and notices; its executable files are discarded. Preparation validates exact
hashes for the archive and each local build artifact and applies the page CSP.
Generated `vendor/` assets are not tracked in Git. The rebuilt File bridge and
provider restrictions went live in release `0eb7730ce9b2c17fcab679da996c99406f2dc1878662ee27d0da7a531664e3e6`.
When upgrading, review the new source and dependency licenses, update the pins,
and repeat the workflow and network tests.

The editor starts in local mode with a new blank design; no Foundry account is needed. Use the editor's **File** menu. **Open from My files** opens account files; upload from a computer in Files first. **Open example…** loads the bundled heart SVG. **Save project** saves to `/Embroidery.stitchfoundry`; **Save project as…** lets you choose a different path in My files. Saves check versions and ask before replacing an unrelated file. The editor's native save/export is also captured inside the window. Choose a result under **Captured editor files**, then use **Save selected captured file…** to persist it. Captured results may represent an earlier editor state. **Export stitches to My files…** exports the current design in the selected machine format and reports warnings. Review the result and test-sew it. The live rebuilt editor removes browser provider transport and blocks eight identified account/AI commands, with CSP as a separate restriction. Those features remain unavailable pending an internal replacement; see `docs/DEFERRED_APP_FEATURES.md`. Further review of the upstream service surface remains open. The app warns about known unsaved edits, but the embedded editor's state and unusual asynchronous operations are not guaranteed to be detected. The app is not a security sandbox.

## Local-only browser source

`prepare_local_source.py` applies a fail-closed patch to a clean checkout of
candidate source commit `e5a88e038d4281c925c94538c1a2d6262b83b83f`. It removes
the browser provider transport and secret store, removes provider commands from
browser menus and the command palette, rejects their direct command IDs, and
hides the StitchShop action in the jobs panel, and removes the MakerFoundry startup-link importer. It preserves those controls in
native builds. The browser availability check hides the prompt and redraw panel
buttons when the provider service is absent.

The rebuilt source is deliberately separate and is not shown to match the older pinned upstream archive. The existing page CSP remains a
separate restriction. Before using a rebuilt binary, verify all browser entry
points and ordinary open/edit/save/export workflows, inspect phone and desktop
UI, and review the remaining network surface and dependency licenses. The `CODI_LOCAL_ONLY_CANDIDATE=1` option in
`tests/embroidery-provider-policy.test.mjs` checks that the provider commands
are absent from the catalog and reject direct execution; it does not replace
visual or network checks.

For a rebuild, check out the pinned commit in a disposable clean source tree,
then run `python3 apps/system/embroidery-studio/prepare_local_source.py PATH`
from SIMPLIFIED. From that checkout's `apps/vectorcraft-web` directory run
`trunk build --release`; its Trunk configuration writes `dist/web` at the
checkout root. The tested build used Rust 1.97, Trunk 0.21.14,
wasm-bindgen 0.2.129 and wasm-opt version_123, with Cargo.lock unchanged.
Inspect and copy the three resulting files into a separate bridge-build directory.
The exact pinned hashes must match; a different toolchain or source may need a
new review and new pins. The archive's notices are retained. The four license texts for epaint's embedded fonts are packaged separately from the exact 0.36.2 crate. The packaged dependency-notice collection covers the conservative resolved graph; review nested assets and source availability before deployment.

## Integration test

From the SIMPLIFIED directory, the currently retained pinned archive is
`.build/stitchfoundry-web-latest.zip` (the SHA-256 above). The archive and
prepared `vendor/` are generated build inputs and are not tracked in Git.
With that archive and the other app build dependencies prepared:

```sh
python3 apps/system/embroidery-studio/prepare.py --archive .build/stitchfoundry-web-latest.zip --local-dist PATH_TO_BRIDGE_DIST --source-archive PATH_TO_MATCHING_SOURCE.zip
../active-system/.venv/bin/python active-system/scripts/build-public-apps.py --output .build/embroidery-test-apps --apps embroidery-studio stitch-converter --node ../active-system/.build/tools/node-v24.22.1-linux-x64/bin/node
../active-system/.venv/bin/python -B active-system/scripts/run-simplified-local.py --port 18159 --isolated --browser-relay --apps-bundle .build/embroidery-test-apps
```

Preparation refuses to replace an existing `vendor/`: omit the first command
if the correct pinned assets have already been prepared. In another shell,
start a disposable Chromium with remote debugging on port 19255, then run:

```sh
../active-system/.build/tools/node-v24.22.1-linux-x64/bin/node tests/embroidery-desktop.test.mjs
CODI_PHONE=1 ../active-system/.build/tools/node-v24.22.1-linux-x64/bin/node tests/embroidery-desktop.test.mjs
```

The test creates isolated test accounts, opens both apps, verifies a converter
preview and PES save, and creates a simple rectangle through the upstream API
to check a DST export to My files. A separate test invokes the embedded editor's Save As command, saves the captured project to an isolated account,
checks server disk, reopens it and exports stitches:

```sh
../active-system/.venv/bin/python -B active-system/scripts/run-simplified-local.py --port 18166 --isolated --browser-relay --apps-bundle .build/embroidery-test-apps
../active-system/.build/tools/node-v24.22.1-linux-x64/bin/node tests/stitchfoundry-native-save.test.mjs
```

The captured Save As test needs the preview and Chromium started in separate shells. It does not verify
digitizing through the editor's own drawing tools, physical devices or stitch
quality. The embedded upstream editor is crowded on narrow phone screens;
physical phone usability remains unverified.
`CODI_TEST_URL` and `CODI_BROWSER_URL` can override the preview and debugging
addresses. Stop the isolated preview and browser and remove their disposable
test data after testing.

A separate notice shows when My files detects that the linked project changed, is unavailable, or has conflicting copies; the current design remains open. Resolve conflicts in Files or save a copy. Overwrite checks use file metadata. Project, captured-file and machine-export destinations are captured when the action starts, and immediate conflicts are reported as local copies needing resolution. Detection depends on mirror sync. Local desktop, emulated-phone and 4K and live emulated-phone account tests cover a changed project, conflict during save, destination changes, a DST export and fresh-session recovery; the existing local native capture/reopen/export test also passed.

The earlier `e5a88e0` no-startup-link candidate passed desktop and emulated-phone startup, same-origin and blocked cross-origin checks. Eight named provider/account commands are absent from its command catalog and direct execution rejects them. Desktop and emulated-phone tests saved a project, synchronized it, exported DST stitches and reopened the project in a fresh session; a separate test also exercised the example and Stitch Converter. The candidate was initially assembled in an isolated test directory; its source revision is a deliberate new build, not a proven match for the older shipped binary. The later build with the My files bridge is now live; broader review of other service entry points and physical touch remains open.

The normal app preparation and builder path passed desktop and emulated-phone provider-policy, save, sync, DST export and fresh-session reopen tests. Preparation rejected a tampered build and refused to overwrite existing vendor files. The later File bridge build is live; remaining network and nested-asset review is ongoing.

The earlier rebuilt no-startup-link candidate used WASM SHA-256 `219d4eb0093438da1656a5c554dabce533382e85938b11140623203e1cc63f0b`. Freshly patched source matched the build tree. Local desktop and emulated-phone tests confirmed no MakerFoundry request from an `open` startup link, blocked provider commands, save, sync, DST export and reopen. The first startup-link test incorrectly matched the local page URL containing the encoded link; the corrected hostname check passed. The current live bridge hash is recorded below.

The current local candidate also guards edits made while an open or example confirmation is displayed and avoids competing Save As prompts. Desktop, emulated-phone and 4K local tests cover cancellation, changed targets, two-session project-change warnings, saving a copy, fresh-session reopen and listener cleanup. The broader dependency-notice review remains open; see `docs/EMBROIDERY_DEPENDENCY_INVENTORY.md`.

Dependency notices for the 317-package conservative WASM normal/build graph are in `licenses/RUST_DEPENDENCY_NOTICES.txt`, including upstream texts matched to exact source revisions for packages whose published crate omitted root license files. Generate metadata with `cargo metadata --offline --locked --format-version 1 --filter-platform wasm32-unknown-unknown` on the pinned source, then run `python3 apps/system/embroidery-studio/collect_dependency_notices.py --metadata PATH --output PATH`. The collector reads the resolved crate cache and fetches pinned upstream notices; compare the generated SHA-256 with the pin in `prepare.py`. This is not a substitute for reviewing nested asset notices and distribution requirements.

The File menu includes **Editor source and licenses**, a pinned archive of the exact patched StitchFoundry checkout and desktop integration sources. To recreate it, run `prepare_source_archive.py --source PATH_TO_PATCHED_CHECKOUT --host-source apps/system/embroidery-studio --output PATH.zip`. It rejects a different commit, unexpected changes or mismatched patches and excludes generated builds and dependency caches. The archive does not bundle dependency source; Cargo.lock and the accompanying dependency notice collection identify those dependencies. The exact host packaging script is distributed alongside the source archive as `prepare.py.txt` (rather than inside the archive, because it pins that archive’s hash).

The live build also applies `prepare_file_bridge.py` after
`prepare_local_source.py` to connect upstream Open and Place to My files.
The bridge WebAssembly SHA-256 is `4599a7093dcb85cc2a8f0a3d4930629eb20524e1c948264af55b4011f5eaa92d`. Rebuild and verify the WebAssembly and corresponding-source archive together; the earlier candidate does not contain this bridge. Open and Place passed local desktop, emulated-phone and 4K account workflows, and a public emulated-phone check; physical touch remains unverified.

The current local File-menu update places opening and saving before the source
link, increases touch targets, and restores focus after dismissing the menu
with Escape. Desktop, emulated-phone and 4K account checks exercised the menu
and My files picker; desktop and emulated-phone checks also exercised Open,
Place, saving, synchronization and a fresh-session reopen. It is not live yet.
Any change to this README or the desktop integration requires regenerating the
corresponding-source archive and updating its pin before release.

Opening or saving a project updates the desktop restore reference; opening the
example clears the prior project reference. A missing or invalid project used
to restore a window clears the failed reference without changing the original
file. Local desktop and emulated-phone account tests cover project switching,
Save As, server sync, refresh and stitch export after reopening; emulated-phone
checks cover invalid and missing project fallback. Physical touch and machine
compatibility remain unverified.

A temporary read failure or conflict when restoring a file keeps its reference
and offers **Retry saved file**. A separate blank scratch design is available;
if the original is the default project filename, Save uses a different recovery
filename. Successful open, save or example selection clears the recovery target.
Desktop and emulated-phone registered-account tests covered an injected read
failure, separate scratch save, server sync, original-byte preservation and retry.
Physical touch, conflict injection and machine stitching remain unverified.
