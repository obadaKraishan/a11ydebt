# Release checklist: a11ydebt v0.1.0

**Nothing in this file has been run.** Every step from step 1 on needs `RELEASE_APPROVED` in the
repo root. Only Obada creates that file, and the hub's release-gate hook blocks publishing
commands without it. The commands below use the documented flags of `gh`, `uv` and `hf`; confirm
each one with `--help` at release time.

## 0. Pre-flight (safe to run any time; publishes nothing)
- [ ] CI is green on `main` for Python 3.10 to 3.13: `gh run list --limit 1`.
- [ ] Local checks pass:
      ```bash
      uv run ruff check . && uv run ruff format --check . && uv run pytest
      ```
- [ ] The reproduction still holds, with each command exiting 0:
      ```bash
      uv run python scripts/compare_aissa.py rico data/interim/audit_rico data/interim/aissa_reference
      uv run python scripts/compare_aissa.py androidcontrol data/interim/androidcontrol/run1 data/interim/aissa_reference
      uv run python scripts/compare_aissa.py bootstrap data/interim/audit_rico data/interim/audit_androidcontrol_run1 data/interim/aissa_reference
      ```
- [ ] The package builds and installs cleanly, and the wheel holds only `a11ydebt/` and its
      dist-info:
      ```bash
      rm -rf dist && uv build && unzip -l dist/a11ydebt-0.1.0-py3-none-any.whl
      ```
- [ ] The versions agree: `__version__`, `CITATION.cff` and `.zenodo.json` all say 0.1.0
      (`tests/test_release_metadata.py` checks this).
- [ ] **Decide what becomes public.** The git history includes `prompts/`, `reports/`,
      `CLAUDE.md`, `docs/roadmap.md` and `docs/session-log.md`. They hold local paths (for example
      `/Volumes/Kraishan/...`) and internal planning notes; the history scan of 2026-11-10 found
      no secrets. Keeping them is the most transparent record of AI-assisted work. Removing them
      means rewriting history, which is a deletion and needs Obada's decision.
- [ ] **Placeholders.** This must list only what is still unknown:
      ```bash
      grep -n PLACEHOLDER CITATION.cff .zenodo.json
      ```
      If the paper DOI does not exist yet, delete the `related_identifiers` entry from
      `.zenodo.json`; Zenodo would reject the placeholder. Keep the commented lines in
      `CITATION.cff`.

## 1. Approval (Obada)
```bash
touch RELEASE_APPROVED    # in ~/research/a11ydebt; it is gitignored and never committed
```

## 2. Make the repository public (Obada runs this)
Check AISSA's blind-review and publication rules first; the paper is accepted, and the
camera-ready is done.
```bash
gh repo edit obadaKraishan/a11ydebt --visibility public --accept-visibility-change-consequences
```
Then open <https://github.com/obadaKraishan/a11ydebt> signed out, and check the README, the CI
badge and the QR code (`docs/assets/qr-a11ydebt.png`).

## 3. Turn on the Zenodo integration (Obada, web UI)
At <https://zenodo.org/account/settings/github/>, sign in with GitHub and switch
`obadaKraishan/a11ydebt` **on**. This must happen *before* the release, because Zenodo archives
only releases published while the switch is on. Zenodo reads `.zenodo.json`, which takes
precedence over `CITATION.cff`.

## 4. Final metadata commit
- `CHANGELOG.md`: change `## [0.1.0] - Unreleased` to `## [0.1.0] - YYYY-MM-DD`.
- `CITATION.cff`: uncomment `date-released` and set it to the same date.
- Then:
  ```bash
  uv run ruff check . && uv run ruff format --check . && uv run pytest
  git commit -am "Prepare the v0.1.0 release" && git push
  ```
- Wait for CI to go green.

## 5. Tag v0.1.0
```bash
git tag -a v0.1.0 -m "a11ydebt 0.1.0"
git push origin v0.1.0
```

## 6. GitHub release (this triggers Zenodo)
```bash
rm -rf dist && uv build
gh release create v0.1.0 dist/a11ydebt-0.1.0.tar.gz dist/a11ydebt-0.1.0-py3-none-any.whl \
  --verify-tag --title "a11ydebt 0.1.0" --notes-file <(sed -n '/^## \[0.1.0\]/,/^## \[/p' CHANGELOG.md)
```
Zenodo mints a version DOI and a concept DOI within minutes; check the Zenodo GitHub page.

## 7. DOI badge and CITATION.cff
- README, under the title:
  `[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.<id>.svg)](https://doi.org/10.5281/zenodo.<id>)`
  (use the concept DOI, so the badge covers every version).
- `CITATION.cff`: uncomment `doi:` and set the concept DOI. Once IEEE Xplore assigns the paper
  DOI, uncomment `doi:` under `preferred-citation` too, and fill both BibTeX notes in the README.
- Validate:
  ```bash
  uvx cffconvert --validate -i CITATION.cff
  grep -n PLACEHOLDER CITATION.cff .zenodo.json
  ```
- Commit and push. Do not move the tag; the DOI files belong to the next version.

## 8. Optional: PyPI
The name `a11ydebt` must be free on PyPI. Use a token from `~/.config/kraishan/secrets.env`, loaded
only inside the shell that publishes, and never printed or committed. Trusted publishing from a
GitHub Actions workflow is the alternative.
```bash
uv publish --publish-url https://test.pypi.org/legacy/ dist/*     # TestPyPI first
uvx --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ a11ydebt --version
uv publish dist/*                                                  # then PyPI
```
Then change the README install line to `pipx install a11ydebt`.

## 9. Optional: Hugging Face Space
This needs a design first, for example a CPU Gradio app that shows `results/v0.1` and audits an
uploaded folder of Rico-format JSON. It must never host Rico data.
```bash
hf repo create obadakr/a11ydebt --repo-type space --space-sdk gradio
hf upload obadakr/a11ydebt space/ . --repo-type space
```

## 10. After the release
- Check the QR code on a phone, signed out.
- Update `~/research/STATUS.md`, `docs/session-log.md` and the AISSA slide (DOI and QR code).
- Suggested: Obada deletes `RELEASE_APPROVED` afterwards, so the next publish needs a fresh
  approval.
