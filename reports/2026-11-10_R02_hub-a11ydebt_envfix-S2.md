# R02 · hub-a11ydebt · envfix-S2
Date: 2026-11-10 · Prompt: prompts/2026-11-10_P02_hub-a11ydebt_envfix-S2.md · From: Claude Code (executor) · To: planner (Claude app)

## 1. Summary (3 lines)
1. **Part A is done.**
   - D1: the release gate is enabled at user level and scoped to `~/research`. You approved the diff, and 166 hub tests pass.
   - D2: the API key is in `secrets.env`. A fresh shell has it unset, and `load_secrets_env()` finds it by name.
   - D3: the Kaggle CLI is installed. D4: `HF_HOME` is set, and the blobs folder was investigated read-only.
   - D5 and D7: the docs are updated. D6 and D8 needed no separate action.
2. **a11ydebt S2 is built.** The AISSA TFRecord reader and AndroidControl parser are ported, with the reader identical field by field. A private Kaggle CPU kernel runs it. **Run 1 reproduces AISSA exactly**: 57.27% needs_label, 62.75% icon_like, every role, all 10 shards, all 7,623 episodes, all 49,888 screens and the 700 apps.
3. **Run 2 is running on Kaggle.** It covers shards 00010 to 00019 as `obadakraishan/a11ydebt-androidcontrol-run2`, status RUNNING at 19:01 UTC with an expected finish around 19:21 UTC. As P02 asks, I did not wait for it.

## 2. Done: what was built, with file paths
**Hub** (`~/research`, private `research-hub`)
- `prompts/2026-11-10_P02_hub-a11ydebt_envfix-S2.md`, plus a copy in `a11ydebt/prompts/`.
- `_shared/hooks/release_gate.py`: scope added. It enforces when the session folder, the folder after any `cd`, or a target path is inside `~/research`. Target paths are `git -C`, `kaggle -p`, an absolute or `~` argument, and the Write/Edit file. Elsewhere it allows everything. The approval is looked for in the repo being published, and `RELEASE_GATE_ROOT` overrides the root for tests. All the R01 additions are kept.
- `_shared/hooks/test_release_gate.py` (20 new scoping tests) and `README.md` (scope, enabled).
- `~/.claude/settings.json` gains the PreToolUse block, saved after you approved the diff.
- `CLAUDE.md`: the Start Here guide is now a plain path read on demand, `@STATUS.md` stays, and the gate and secrets lines are up to date. `STATUS.md` has a11ydebt updated and ai-invisibility-v2 added.

**System files** (not in any repo)
- `~/.config/kraishan/` (700) and `secrets.env` (600) hold `ANTHROPIC_API_KEY`.
- `~/.zshrc` line 19 is now a note pointing to `secrets.env`, and the HF lines are appended.
- `~/.local/bin/kaggle` is the Kaggle CLI 2.2.5 (a uv tool, with `six`).

**a11ydebt** (`~/research/a11ydebt`, private)
- **Library:**
  - `src/a11ydebt/counts.py`: one shared, stdlib-only counting loop.
  - `src/a11ydebt/tfrecord.py`: the port of AISSA's reader.
  - `src/a11ydebt/androidcontrol.py`: the port of AISSA's parse logic and `apps.py`.
  - `src/a11ydebt/kaggle_outputs.py`
  - `coverage.py`: now takes any screen, and `n_apps` excludes the unknown app.
- **CLI:** `a11ydebt audit androidcontrol SHARD...` and `a11ydebt summarize androidcontrol DIR`.
- **Kernel:** `kaggle/androidcontrol_parse/` holds `job.py`, `build_kernel.py`, `config_run1.json`, `config_run2.json` and `README.md`.
- **Scripts:** `scripts/aissa_androidcontrol_reference.py` (new) and `scripts/compare_aissa.py`, which gains an `androidcontrol` mode.
- **Tests:** `tests/synthetic_tfrecord.py` writes synthetic shards (real masked CRC32C, never real data). The suites are `tests/test_tfrecord.py`, `tests/test_androidcontrol.py` and `tests/test_kaggle_job.py`.
- **Docs:** `NOTICE` (provenance of the ported files), `docs/reproduction-androidcontrol.md`, `docs/session-log.md`, `CHANGELOG.md`, `README.md` and `CLAUDE.md` (commands).
- **Data** (gitignored):
  - `data/interim/aissa_reference/androidcontrol_shards.json` lists the 10 shards, with URL, bytes and SHA-256, and the episode ids per shard.
  - Alongside it: AISSA's parse report, episode table and derived per-screen counts.
  - `data/interim/androidcontrol/run1/` holds the pulled kernel output.
  - `data/interim/audit_androidcontrol_run1/` holds the CSV/JSON tables.

## 3. Results: numbers, test results, comparison tables
- **Tests:** hub 166 passed (hook 147, llm_client 19); a11ydebt 80 passed; ruff is clean in both.
- **Reader check:** the ported reader against AISSA's original module, run on the synthetic shard, gave identical records, examples, forests and nodes, field by field.
- **Rico regression:** after the counting refactor, the full Rico audit still reproduces AISSA exactly.
- **Kaggle run 1:** private CPU kernel `obadakraishan/a11ydebt-androidcontrol-run1`, version 1, built from commit `cc969a9`.
  - Pushed at 18:31:58 UTC; `COMPLETE` at the 18:57 check.
  - 1,233 s (20.6 min) on 4 CPUs, about 2 min per shard (about 22 s to download each 2.5 GB, then about 1.5 to 2 min to parse).
  - Python 3.13.18; pinned pyarrow 26.0.1 installed.
  - **Output 12.1 MB:** nodes 11.2 MB (1,462,549 candidate rows) and screens 0.9 MB.
  - 0 failed or truncated shards, 0 episode failures.
- **Kaggle run 2:** `obadakraishan/a11ydebt-androidcontrol-run2`, version 1, built from `3896724` (same bundled modules as run 1). Pushed at 18:59:40 UTC, RUNNING at 19:01 UTC; expected to finish around 19:21 UTC.

**AndroidControl comparison, run 1 against AISSA** (`compare_aissa.py androidcontrol` exits 0)

| Quantity | AISSA | a11ydebt | Match |
|---|---:|---:|:-:|
| Shards / episodes / failed / truncated | 10 / 7,623 / 0 / 0 | 10 / 7,623 / 0 / 0 | yes |
| Screens (observations) | 49,892 | 49,892 | yes |
| Nodes | 11,002,225 | 11,002,225 | yes |
| Included (visible, positive area) | 6,831,063 | 6,831,063 | yes |
| Needs label: candidates / labelled | 1,462,544 / 837,536 | 1,462,544 / 837,536 | yes |
| **needs_label coverage** | **57.27%** | **57.27%** | yes |
| Icon-like: candidates / labelled | 194,529 / 122,074 | 194,529 / 122,074 | yes |
| **icon_like coverage** | **62.75%** | **62.75%** | yes |
| Apps from resource ids (episodes with needs-label elements) | 700 | 700 | yes |

| Role (needs label) | Candidates | Labelled | Coverage | Match |
|---|---:|---:|---:|:-:|
| button | 108,037 | 78,066 | 72.26% | yes |
| image | 1,203,560 | 703,149 | 58.42% | yes |
| input | 24,402 | 6,640 | 27.21% | yes |
| other | 119,895 | 46,654 | 38.91% | yes |
| text | 6,650 | 3,027 | 45.52% | yes |

- **Per shard:** all 10 shards match AISSA's ReviewerChecks table on episodes, needs-label count and coverage. Coverage ranges from 55.84% (shard 00006) to 59.23% (shard 00008).
- **Episodes:** all **7,623 of 7,623** are equal on `n_observations`, `n_elements`, `n_included`, `n_needs_label`, `n_labelled`, `n_icon_like` and `n_icon_like_labelled`.
- **Screens:** all **49,888 of 49,888** non-empty screens are equal on 6 counts, and the 4 screens absent from AISSA's node table have no nodes in a11ydebt either.
- **Apps:** per-episode apps equal AISSA's own `androidcontrol_episode_apps()` for **7,623 of 7,623** episodes, with 253 left without an app in both. Over all episodes there are 701 apps; the extra one, `com.vitotechnology.sky.tonight.map.star.walk`, appears only in episodes with no needs-label elements.

**All three populations, run 1**

| Population | Candidates | Labelled | Coverage | Screens with ≥1 unlabelled |
|---|---:|---:|---:|---:|
| needs_label | 1,462,544 | 837,536 | 57.27% | 49,692 of 49,892 |
| icon_like | 194,529 | 122,074 | 62.75% | 20,779 of 49,892 |
| interactive_image (P01, new) | 133,266 | 78,469 | 58.88% | 15,569 of 49,892 |

## 4. Part A decisions (done or blocked), and the HF blobs findings
| # | Decision | Status |
|---|---|---|
| D1 | Release gate at user level, with all additions, scoped to `~/research` | **Done** (`40ea6b6`). 20 scoping tests; 166 hub tests pass. You approved the `settings.json` diff and it was saved. In a live check, `git push --tags` in `~/research/a11ydebt` exits 2, the same command in `/tmp` exits 0, and a normal `git push` exits 0. |
| D2 | Move `ANTHROPIC_API_KEY` | **Done.** `secrets.env` is 600 and its folder is 700. A fresh interactive zsh shows `ANTHROPIC_API_KEY: unset`, and `load_secrets_env()` returns `['ANTHROPIC_API_KEY']`. Line 19 was **replaced** by a note rather than commented out, so no second plaintext copy is left in `~/.zshrc`. **Please open a new terminal and fully quit and reopen VS Code.** This session still carries the old environment, so I kept unsetting the key per command. |
| D3 | Kaggle CLI | **Done.** `~/.local/bin/kaggle` (CLI 2.2.5); `kaggle datasets list --mine` works. |
| D4 | `HF_HOME` | **Done.** Your guarded line, plus `export HF_TOKEN_PATH="$HOME/.cache/huggingface/token"`. Without it, `hf` would look for the token on the drive and be logged out. A fresh shell has `HF_HOME` on the drive, and `hf auth whoami` returns obadakr. (`HF_STORED_TOKENS_PATH` is derived from `HF_TOKEN_PATH`, so it needs no variable of its own.) |
| D5 | Hub `CLAUDE.md` | **Done** (`2dab95e`). Only `@STATUS.md` is imported, and the file is 79 lines. |
| D6 | Going public | No action. Both repos remain PRIVATE, and the AISSA repo was not touched. |
| D7 | ai-invisibility-v2 in STATUS.md | **Done** (`e34a271`). Its repo was not modified. |
| D8 | 10 shards, then all 20 | **Done.** Run 1 matched exactly, and run 2 is running. |

**HF `hub/blobs` findings (read-only; nothing deleted):**
- **What it is:** the 59 GB top-level folder is a content-addressed dedup store. Its layout is `blobs/<2-hex prefix>/<sha256>`, with a `.refs` file next to each blob naming the repo blob that uses it, and a `.lock` file. It is not xet: there is no `xet/` folder. It is not the standard layout either, where each model keeps regular files in its own `blobs/`.
- **What uses it:** all 24 content files are in use. Twelve models reach them through a second symlink hop: snapshot file, then `models--X/blobs/<etag>`, then `../../blobs/<xx>/<sha256>`. The 12 are falcon-7b, falcon-7b-instruct, RADAR-Vicuna-7B, gpt-neo-2.7B, gpt2-xl, bge-m3, nllb-200-distilled-600M, MAGE, desklib ai-text-detector, roberta-base-openai-detector, tmr-ai-text-detector and modernbert-ai-detection-raid-mage. The largest blobs are 10.7, 10.0, 10.0, 6.4, 4.5 and 4.5 GB.
- **Risk:** removing the folder would break those 12 models. It looks like an earlier dedup step (created around Nov 6 to 7). Tools like `hf cache delete` may not understand this layout, so don't clean this cache with them.

## 5. Commits: hash + message, and whether pushed
Every commit carries the Co-Authored-By trailer and was pushed right after it was made.

| research-hub | Message |
|---|---|
| b6d0d7f | Add the P02 prompt (environment fixes and a11ydebt S2) |
| 40ea6b6 | Scope the release gate to ~/research and enable it at user level |
| 2dab95e | Stop importing the Start Here roadmap in CLAUDE.md (D5) |
| e34a271 | Add ai-invisibility-v2 to STATUS.md as a paper project (D7) |
| (this commit) | Add the R02 report and update STATUS.md |

| a11ydebt | Message |
|---|---|
| 709038b | Add the P02 prompt (copy of the hub prompt) |
| 1a2a7dd | Share per-screen counting between corpora in a11ydebt.counts |
| 9b96edf | Port the AISSA AndroidControl reader and parser |
| 2964209 | Add the AISSA AndroidControl reference builder (dev-only) |
| cc969a9 | Add the AndroidControl Kaggle kernel (private CPU script) |
| ad96c33 | Add `a11ydebt summarize androidcontrol` for Kaggle outputs |
| ff7472b | Extend compare_aissa.py with an AndroidControl mode |
| f610cdf | Update the changelog and project commands for S2 |
| 3896724 | Count AndroidControl apps the AISSA way; fix the run summary app total |
| 8c2754f | Do not count screens without an identified app as an app |
| 7bc1a8e | Record the S2 AndroidControl reproduction and update the docs |
| (next commit) | Add a copy of the R02 report |

## 6. Problems and how you handled them
1. **D2 wording.** Literally commenting out line 19 would have left the key in plaintext inside `~/.zshrc`, so I replaced the line with a note, as the approved plan said.
2. **D4 side effect.** `HF_HOME` alone would have logged `hf` out, so I added `HF_TOKEN_PATH` and verified that `whoami` still works. This also corrects my plan, which wrongly listed `HF_STORED_TOKENS_PATH` as a variable to set.
3. **No CPU machine_shape on Kaggle.** Kaggle documents only GPU and TPU shape names, so I set `machine_shape` to `""` explicitly, with GPU and TPU off. That is the CLI template's own convention.
4. **App count 701 against 700.**
   - **Cause:** a definition gap. AISSA counts apps over episodes that have needs-label elements.
   - **Fix:** the comparison now uses AISSA's definition. I also verified the per-episode apps with AISSA's own function.
5. **Two reporting bugs, fixed before run 2.**
   - **Run summary:** run 1's `run_summary.json` summed per-shard distinct app counts (2,967). It now counts distinct apps across shards.
   - **App total:** `n_apps` counted the unknown app as an app (702 instead of 701).
   - Neither bug touched any coverage count.
6. **Small slips, both fixed.** I committed the reference script with one over-long line and fixed it in the next commit. During plan-mode exploration I wrote a stray `/tmp/claude_present.txt`, which I removed.
7. **Logs while running.** `kaggle kernels logs` prints nothing without `-f` while a kernel runs, and macOS has no `timeout`, so I sampled the live log with `perl -e 'alarm N'`.

## 7. Decisions I need to make (numbered questions)
1. **Restart check:** after reopening VS Code and your terminals, does `[ -n "${ANTHROPIC_API_KEY+x}" ] && echo set || echo unset` print `unset` in a new Claude Code session?
2. Your HF token files (`~/.cache/huggingface/token` and `stored_tokens`) are mode **644**, so other local users can read them. May I `chmod 600` them?
3. **HF dedup store:** should I leave it as is (my recommendation, since it is in use), or write a short note in `AI-Models/` explaining the layout so future cleanups don't break the 12 models?
4. **Run 2:** pull it in a short follow-up session with `kaggle kernels output obadakraishan/a11ydebt-androidcontrol-run2 -p data/interim/androidcontrol/run2`, then `uv run a11ydebt summarize androidcontrol data/interim/androidcontrol --out data/interim/audit_androidcontrol_all20` for the all-20 totals. Or fold that into the next prompt?
5. Should S3 or S4 add streaming straight from Rico's `unique_uis.tar.gz` (6.5 GB)? Users then wouldn't need the 16 GB extraction.
6. **P03 (reliacode):** its preconditions are now met (the gate is enabled and the secrets are fixed). Run it in a fresh session started from `~/research`, after the restart in question 1.

## 8. Usage note: rough share of the session limit this used
I can't read the meter. P02 took about 110 tool calls in a context already long from P01, plus roughly 3,000 lines of code, tests and docs. My rough guess is a third to half of a 5-hour Max window; check `/usage`. The heavy work ran elsewhere and cost no Claude usage: about 50 GB of downloads and parsing on Kaggle, and a 7-minute Rico regression run locally. Status checks ran as background loops.

## 9. Suggested next prompt scope
**P04 · a11ydebt follow-up and S3** (fresh session from `~/research/a11ydebt`):
- Pull run 2 and report the all-20-shard AndroidControl table, which has no AISSA counterpart.
- **S3, bootstrap:** port AISSA's cluster bootstrap by app (`src/a11ydebt/bootstrap.py`). For AndroidControl, an episode with no app is its own cluster, as in AISSA. Reproduce the ReviewerChecks `clustered_coverage` intervals.
- **S3, report:** `a11ydebt report` writes Markdown and CSV tables for both corpora.

P03 (reliacode) can run in parallel in its own fresh session.
