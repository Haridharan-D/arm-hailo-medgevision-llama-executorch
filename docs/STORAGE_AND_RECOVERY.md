# Storage cleanup and recovery boundary — 26 November 2026

**GitHub is the deployment/evidence repository, not a complete backup of the original laptop workspace.** Do not interpret a clean Git status as proof that ignored/untracked training data, private records or unrelated projects have been backed up.

## Available in this repository

- Application/API/UI/native source, training/export notebooks and conversion recipes.
- Five complete frozen vision models in their deployment paths. The original Arm runtime and library are reconstructed from verified Git parts.
- Model contracts, fixed thresholds, manifests, historical metric files and final eight-case target records.
- Forty-seven actual Pi screenshots, final project PDF and measured output/advisory evidence.
- A verified portable eight-record SQLite/image/advice backup with safe restore tooling.
- Tests, CI, deployment instructions and pinned Llama download recipe.

## External or private material

- The large Llama PTE/tokenizer are downloaded externally; they are not stored as Git blobs.
- Original training checkpoints/submission archives and raw datasets are not all in Git.
- The complete private Pi archive and database/account files are deliberately not published.
- User videos, report-review files, unrelated projects and untracked/ignored files are not guaranteed by this repository.

## Local preservation copy

Before cleanup on 26 November, selected essential Medge Vision files were copied outside both original project trees to `C:/MEDGE_VISION_KEEP_20261126` with source/destination SHA-256 verification. Its `PRESERVATION_MANIFEST.json` identifies exactly what was copied. It includes private Pi recovery, report review, pinned Llama artifacts, final YOLO best/last checkpoints, three final anomaly submission archives and Git-history bundles.

This directory is **private local recovery**, not a GitHub upload and not an independent-disk backup. Keep it and make an independent copy before erasing the disk. It does not claim to preserve every file in the surrounding workspace, unrelated projects, raw datasets or later user videos.

To restore repository history from the retained bundle:

```sh
git clone C:/MEDGE_VISION_KEEP_20261126/MedgeVision_all_refs.bundle MedgeVision_recovered
```

The bundle is a point-in-time copy. Use GitHub for later documentation updates. For inspection data recovery, follow the retained private archive instructions or the [published portable restore guide](../backups/README.md). Neither creates a bootable SD-sector image.

**Safe cleanup applies only to files whose recovery sources have been independently verified. No deletion or formatting was performed by this verification.**
