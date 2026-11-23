# Optional Google Drive mirror — NOT PUBLISHED/VERIFIED

Requested folder: https://drive.google.com/drive/folders/1XthIj5jxT8l2tZ4H0GsnuLCdJ7WaervG

The audit session had no Drive upload connector and could not read that folder through its web tool. No model upload, sharing change or working Drive file ID is claimed. The folder ID is not a downloadable model file ID. Primary vision artifacts remain complete in Git model parts; the pinned Llama downloader remains the working external-artifact recipe.

If the owner mirrors a licensed artifact, copy the exact local file without modifying it, preserve licensing and record its individual shared file ID. The Llama file is at `C:/arm_bharath_soc_2027/BlisterTrace_App/llama/artifacts/Llama-3.2-1B-Instruct-SpinQuant_INT4_EO8.pte`. Expected identities are in ARTIFACT_MANIFEST.json. Do not upload passwords, users files or private inspection evidence.

Once an individual file ID is available:

```sh
python -m pip install 'gdown>=5,<6'
python tools/download_drive_artifact.py --artifact llama/artifacts/Llama-3.2-1B-Instruct-SpinQuant_INT4_EO8.pte --file-id ACTUAL_SHARED_FILE_ID
python tools/verify_repository_artifacts.py
```

This optional adapter validates full size and SHA256 before publishing the downloaded file. It is syntax-checked but end-to-end Drive transfer is NOT TESTED. It never replaces hash validation with a successful HTTP response. Users can continue to use `python llama/download_model.py` instead.
