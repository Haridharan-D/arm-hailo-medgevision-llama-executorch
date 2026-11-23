# Backup audit — 23 November 2026

**NOT CLEARED TO ERASE THE ORIGINAL SD CARD.**

Laptop copies verified present: application source, web designs, tests, compiled Hailo HEF, YOLO ONNX, all three EfficientAD ONNX models, Llama 1B PTE and historical validation reports. Model hashes are recorded in ARTIFACT_MANIFEST.json. PTE remains at C:/arm_bharath_soc_2027/BlisterTrace_App/llama/artifacts on this laptop and is excluded from Git.

SD detected as PhysicalDrive1, SDHC 31,914,983,424 bytes, FAT32 boot + Linux root partition. Raw read-only access was denied. No SD contents were modified. Laptop had only about 5.9 GB free, insufficient for a full 31.9 GB image.

Not verified backed up: active final aarch64 instrumented executable/shared library, production config, complete ~/BlisterTrace_Data SQLite/images/spool, terminal demo session data, user service/launchers and OS dependencies. Historical reports are not a substitute for those files.

Keep the SD intact until a read-only backup is made on a machine able to read ext4, or a full disk image is saved to a drive with at least 32 GB free and verified. Never format based only on successful Git push. Do not place private users/credentials/evidence databases in a public repository.
