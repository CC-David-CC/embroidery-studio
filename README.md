# Embroidery Studio

This app packages an upstream StitchFoundry 0.14.0 development browser build
(MIT OR Apache-2.0), associated with source commit
`e3b80b2ce3f5a3e9cabd00a4d4824b65dc35a017`. The upstream web archive
SHA-256 is `ebcba487093c414e57d634beff032ad60b300c8296f8fbaf44993920ff60c6c6`.
Its upstream notices and font licenses are included in the packaged assets.
The upstream project describes the build as pre-release and reports software
round trips but no physical-machine sew-out yet; test on fabric before relying
on an export. Individual format behavior must be verified independently.

Fetch `stitchfoundry-web-0.14.0.zip` from the official latest-build release, then run
`python3 apps/system/embroidery-studio/prepare.py --archive PATH`. The script
checks the exact hash, safely extracts known assets and moves the startup module
to a same-origin external file for the desktop CSP. The generated `vendor/`
files stay out of Git; the app manifest, preparation code and documentation
are source. To upgrade, review the new release, licenses and API, update the
pin and repeat testing before changing the shipped version. The latest-build
asset can change upstream, so preserve the archive matching this hash.

Open account files with **Open from My files**. The editor's native save/export
is captured inside the editor window instead of downloading to the computer;
choose the captured result and use **Save to My files** to persist it. The
**Export stitches to My files** control directly exports the current design
to the chosen machine format and account path. It reports export warnings;
review the result and test-sew it. The app reports local save and background
server sync separately. Closing before
that step can lose captured work. Uploading from the computer remains an
upstream editor feature. The app is not a security sandbox.

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
to check a DST export to My files. It does not test digitizing through the
editor's own UI, native save capture, physical devices, or stitch quality.
`CODI_TEST_URL` and `CODI_BROWSER_URL` can override the preview and debugging
addresses. Stop the isolated preview and browser and remove their disposable
test data after testing.
