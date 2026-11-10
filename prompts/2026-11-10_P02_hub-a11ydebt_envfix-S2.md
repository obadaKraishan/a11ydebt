# P02 · Environment fixes + a11ydebt Session 2 (AndroidControl on Kaggle)
Date: 2026-11-10 · From: planner (Claude app) · To: Claude Code (executor)
Follow the protocol in ~/research/CLAUDE.md: save this prompt first (hub prompts/ for Part A context, and a copy in a11ydebt/prompts/), plan mode, small commits pushed after each step, report at the end.

## Part A · Decisions from R01 (do these first, in order)
D1 Release gate: enable it at user level (~/.claude/settings.json) with ALL the additions you listed in R01. One change: the hook only enforces when the working directory or the target path is inside ~/research, so my other projects (client websites, teaching) are unaffected. Add tests for that scoping, re-run the full hook test suite, then show me the final settings.json diff before saving it.
D2 ANTHROPIC_API_KEY: yes, do it. Create ~/.config/kraishan/secrets.env (chmod 600), move the key there, and comment out ~/.zshrc line 19 with a note pointing to secrets.env. Never print the key value; refer to it by name only. Then tell me to open a new terminal, and confirm in a fresh shell that the variable is unset and that llm_client's load_secrets_env() still finds it by name.
D3 Kaggle CLI: install permanently with `uv tool install kaggle --with six --python 3.12`, then verify with `kaggle datasets list --mine`.
D4 HF_HOME: add to ~/.zshrc, guarded so it only applies when the drive is mounted:
   `[ -d /Volumes/Kraishan/AI-Models ] && export HF_HOME=/Volumes/Kraishan/AI-Models/huggingface`
   Then investigate the 59 GB top-level hub/blobs folder READ-ONLY: what references it (snapshot symlinks, a newer cache layout, xet), which models or datasets it belongs to, and whether anything would break if it were removed. Report findings. Delete nothing.
D5 Hub CLAUDE.md: replace the @import of docs/roadmaps/00_Start_Here_ZeroCash.md with a plain path that you read only when needed. Keep @STATUS.md.
D6 Going public: both repos stay private for now. a11ydebt goes public at v0.1 (S4, target Dec 1) after I confirm. I will check the CogMI title on AISSA commit 20c12c3 myself; do not touch the AISSA repo.
D7 Add ai-invisibility-v2 to STATUS.md as "paper project, not one of the 10 artifacts". Do not modify its repo.
D8 Yes: reproduce AISSA's AndroidControl numbers on the same 10 shards first, then run all 20.

## Part B · a11ydebt Session 2: AndroidControl on Kaggle
Goal: reproduce AISSA's AndroidControl numbers on Kaggle, then extend the audit to the full corpus.
1. Port AISSA's pure-Python TFRecord/protobuf reader (src/a11ydebt/tfrecord.py in the AISSA repo) and its AndroidControl parse logic into a11ydebt.androidcontrol. Same codebook and the same three populations as Rico. Tests on small synthetic TFRecords you generate (never commit real data). Record the ported code's provenance in NOTICE.
2. From the AISSA repo and outputs, identify exactly which 10 shards and episode IDs AISSA used. Save that list to data/interim/aissa_reference/androidcontrol_shards.json.
3. Build kaggle/androidcontrol_parse/ as a private CPU script kernel (no GPU needed):
   - downloads one shard at a time from the public gs://gresearch/android_control/ bucket over HTTPS, parses it, writes per-screen counts to Parquet, then deletes the raw shard before fetching the next
   - writes per-node rows only for candidate nodes (needs_label, icon_like, interactive_image) to keep output small; estimate total output size first and tell me if it would exceed 10 GB
   - checkpoints after every shard and is resumable (skips finished shards); exits cleanly before the 12-hour limit
   - takes the shard list from a config file, so run 1 = AISSA's 10 shards and run 2 = the other 10
   - pins package versions, sets machine_shape explicitly, and is_private: true
4. Test the kernel script locally on one small synthetic file, then push it and start run 1.
5. Polling: do not burn session usage. Check status at long intervals. If the run will take hours, tell me the expected finish time and stop; I will start a short follow-up session to pull results.
6. When outputs are ready, pull them with `kaggle kernels output`, extend scripts/compare_aissa.py for AndroidControl, and compare against AISSA: 57.27% needs_label (837,536/1,462,544) and 62.75% icon_like (122,074/194,529). Report the full table plus interactive_image numbers.
7. If run 1 matches, start run 2 (the remaining 10 shards), report its kernel slug and status, and do not wait for it to finish.

## Report
Usual template. Include: each Part A decision (done or blocked), the HF blobs findings, kernel slug, runtime and output size, and the AndroidControl comparison table.
