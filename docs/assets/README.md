# docs/assets

| File | What | How it was made |
|---|---|---|
| `qr-a11ydebt.png` | QR code for <https://github.com/obadaKraishan/a11ydebt> (444 × 444 px, error correction M) | `uvx segno "https://github.com/obadaKraishan/a11ydebt" --error=m --scale=12 --border=4 --output=docs/assets/qr-a11ydebt.png`, checked by decoding it with zxing-cpp. segno is a dev-only tool run through uvx; it is not a project dependency. |

The QR code points at the repository, which is private until the release. Before printing it,
check that the link works for a signed-out visitor.
