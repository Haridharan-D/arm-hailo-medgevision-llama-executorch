# Verified backups and restoration

## Included in Git: portable measured demo backup

BUNDLE_MANIFEST.json and demo_recovery.*.part contain a complete credential-free demo data directory: eight actual measured inspections, original/source images, annotated images, six heatmaps/raw maps, validated recorded Llama advice, SQLite history and an independently verified recovery audit chain. They do not contain users.json, passwords, sessions or unrelated station history. The audit chain is a NEW import chain; it is not represented as the original full station chain. Original measurements/IDs are preserved.

```sh
python tools/restore_demo_backup.py --output restored-demo
```

The command checks every part, full archive and restored file hash, refuses existing output directories, rejects path traversal, and verifies SQLite/audit/image integrity. It does not overwrite current station data. After installing requirements and model artifacts, preview the restored history on Linux:

```sh
BLISTERTRACE_DATA="$PWD/restored-demo" python run.py
```

PowerShell:

```powershell
$env:BLISTERTRACE_DATA="$PWD/restored-demo"
python run.py
```

Open History, select an inspection and review its image/heatmap/advice. These are archived measured results, not a new inference. Use ~/medge-test or the source demo commands for new inference. The archive does not contain the large model files: model parts and the pinned Llama download are documented in QUICKSTART.md.

## Complete private station recovery

The complete 308,138,078-byte station archive and post-validation delta are separately retained at C:/Arm_B_PS5/Arm_Hailo_Models/Pi_Recovery_20261124. Their per-file and archive verification receipts are in evidence/target_20261124/BACKUP_VERIFIED.json. The private archive contains accounts, all inspection history and station configuration, and is deliberately NOT published to GitHub. It is project recovery, not a bootable SD image.

Preserve both archives, their manifests, original model folders and RESTORE_PROJECT.md in that private directory. On the original user/home restore the original data subtree first and the delta second, then install the clone service using current code and verified artifacts. Review absolute paths if username/home changes. Never blindly enable an archived systemd unit pointing at a missing old virtualenv. New inspections after the snapshot need a new private backup.
