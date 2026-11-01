# Embroidery Studio

This app packages an upstream StitchFoundry 0.14.0 development browser build
(MIT OR Apache-2.0), associated with source commit
`e3b80b2ce3f5a3e9cabd00a4d4824b65dc35a017`. The upstream web archive
SHA-256 is `ebcba487093c414e57d634beff032ad60b300c8296f8fbaf44993920ff60c6c6`.
Its upstream notices and font licenses are included in the packaged assets.
The upstream project describes the build as pre-release and reports software
round trips but no physical-machine sew-out yet; test on fabric before relying
on an export. Individual format behavior must be verified independently.

The earlier `0.14.0-rc.1` browser build panicked in Rust's system-time
implementation. The pinned newer development build avoids that observed panic
in the tested workflows; it is still pre-release software.

Fetch `stitchfoundry-web-0.14.0.zip` from the official latest-build release, then run
`python3 apps/system/embroidery-studio/prepare.py --archive PATH`. The script
checks the exact hash, safely extracts known assets and moves the startup module
to a same-origin external file for the desktop CSP. The generated `vendor/`
files stay out of Git; the app manifest, preparation code and documentation
are source. To upgrade, review the new release, licenses and API, update the
pin and repeat testing before changing the shipped version. The latest-build
asset can change upstream, so preserve the archive matching this hash.

The editor starts in local mode with a new blank design; no Foundry account is needed. Use the editor's **File** menu. **Open from My files** opens account files; upload from a computer in Files first. **Open example…** loads the bundled heart SVG. **Save project** saves to `/Embroidery.stitchfoundry`; **Save project as…** lets you choose a different path in My files. Saves check versions and ask before replacing an unrelated file. The editor's native save/export is also captured inside the window. Choose a result under **Captured editor files**, then use **Save selected captured file…** to persist it. Captured results may represent an earlier editor state. **Export stitches to My files…** exports the current design in the selected machine format and reports warnings. Review the result and test-sew it. The upstream Sign In action is replaced by a Local label. Provider-backed AI and account features stay unavailable and are listed in `docs/DEFERRED_APP_FEATURES.md`; they are blocked pending an internal service. The app warns about known unsaved edits, but the embedded editor's state and unusual asynchronous operations are not guaranteed to be detected. The app is not a security sandbox.

## Integration test

From the SIMPLIFIED directory, the currently retained pinned archive is
`.build/stitchfoundry-web-latest.zip` (the SHA-256 above). The archive and
prepared `vendor/` are generated build inputs and are not tracked in Git.
With that archive and the other app build dependencies prepared:

```sh
python3 apps/system/embroidery-studio/prepare.py --archive .build/stitchfoundry-web-latest.zip
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
