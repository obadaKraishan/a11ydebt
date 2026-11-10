# kaggle/androidcontrol_parse

This private Kaggle **CPU** script kernel parses AndroidControl's 20 GZIP TFRecord shards (about
50 GB) with a11ydebt's codebook. It writes compact Parquet outputs. Nothing large comes to the
laptop.

| Run | Config | Shards | Purpose |
|---|---|---|---|
| run 1 | `config_run1.json` | 00000-00009, 25.3 GB, SHA-256 from AISSA | Reproduce AISSA: 57.27% needs_label, 62.75% icon_like |
| run 2 | `config_run2.json` | 00010-00019, 24.7 GB, MD5 from GCS | Extend the audit to all 20 shards |

## What the job does (`job.py`)
For each shard:
1. **Skip** it if `shards/<name>.json` already exists.
2. **Stop cleanly** if time is short. The budget is 11 h against Kaggle's 12 h limit, and the job stops when less than 1.5 times the slowest shard is left.
3. **Download** it over HTTPS from `storage.googleapis.com/gresearch/android_control/` to `/tmp`, not to the saved output. Verify bytes and checksum, with 3 attempts.
4. **Parse** it, then write:
   - `screens/<name>.parquet`: one row per screen, with counts for all three populations and a needs_label split by role.
   - `nodes/<name>.parquet`: only nodes in at least one population.
   - `shards/<name>.json`: the checkpoint marker.
5. **Delete** the raw shard.

At the end it writes `run_summary.json`, with the status, totals, versions, timings and output size.

**Estimated output:** about 20 to 70 MB per run (about 50k screen rows and about 1.5M node rows), well under the 10 GB limit.

## Build, push, poll, pull
```bash
cd ~/research/a11ydebt
uv run python kaggle/androidcontrol_parse/build_kernel.py kaggle/androidcontrol_parse/config_run1.json
kaggle kernels push -p kaggle/androidcontrol_parse/build/run1
kaggle kernels status obadakraishan/a11ydebt-androidcontrol-run1     # check about every 10 minutes
kaggle kernels output obadakraishan/a11ydebt-androidcontrol-run1 -p data/interim/androidcontrol/run1
uv run a11ydebt summarize androidcontrol data/interim/androidcontrol/run1 --out data/interim/audit_androidcontrol_run1
```

## Pinning and settings
- **Code:** `run.py` bundles a11ydebt's stdlib-only modules and `job.py` at a recorded git commit (`BUILD`).
- **pyarrow:** pinned to the version used by the local tests. It is installed into `/tmp/a11ydebt_pkgs` when the image's version differs.
- **Image:** `docker_image_pinning_type: "original"` keeps later versions on the first run's image.
- **Machine:** CPU only, via `enable_gpu: false`, `enable_tpu: false` and `machine_shape: ""`. Kaggle has no named CPU shape.
- **Access:** `is_private: true`. `enable_internet: true` is needed to reach the bucket.

## Local test
`tests/test_kaggle_job.py` runs the job and the built `run.py` on a synthetic shard over `file://` URLs:
- outputs
- resume
- bad checksum
- time-budget stop
- kernel metadata
