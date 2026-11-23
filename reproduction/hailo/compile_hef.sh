#!/usr/bin/env bash
set -euo pipefail
TASK_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$TASK_DIR/.." && pwd)"
COMPILER_ROOT="${BT_HAILO_BUILD_ROOT:-$HOME/blistertrace_hailo_compiler}"
MODEL="${MEDGE_ONNX:-$TASK_DIR/../../assets/blistertrace_yolov8s.onnx}"
CALIB="${MEDGE_CALIBRATION:?Set MEDGE_CALIBRATION to the original 512-image training-only calibration folder}"
OUT="$TASK_DIR/output"
VENV="$COMPILER_ROOT/venv311"
test -x "$VENV/bin/hailomz"
test -s "$MODEL"
test -f "$CALIB/calibration_manifest.json"
mkdir -p "$OUT"
"$VENV/bin/python" - "$MODEL" "$CALIB" <<'PY'
import hashlib,json,sys
from pathlib import Path
import onnx
model=onnx.load(sys.argv[1]);shape=[x.dim_value for x in model.graph.input[0].type.tensor_type.shape.dim]
assert shape==[1,3,640,640],shape
root=Path(sys.argv[2]);manifest=json.loads((root/'calibration_manifest.json').read_text())
assert len(manifest)==512
for row in manifest:
    assert row['origin']=='train_only'
    assert hashlib.sha256((root/row['file']).read_bytes()).hexdigest()==row['sha256']
print('Verified static 640x640 graph and 512 training-only calibration images.')
PY
cd "$OUT"
# Official v2.19.1 Model Zoo CLI, custom YOLOv8s checkpoint and seven classes.
# The Model Zoo owns input normalization and creates HailoRT NMS postprocessing.
"$VENV/bin/hailomz" compile yolov8s \
  --ckpt "$MODEL" --hw-arch hailo8 --calib-path "$CALIB" --classes 7 \
  --end-node-names \
  /model.22/cv2.0/cv2.0.2/Conv /model.22/cv3.0/cv3.0.2/Conv \
  /model.22/cv2.1/cv2.1.2/Conv /model.22/cv3.1/cv3.1.2/Conv \
  /model.22/cv2.2/cv2.2.2/Conv /model.22/cv3.2/cv3.2.2/Conv \
  2>&1 | tee compilation.log
test -s "$OUT/yolov8s.hef"
cp "$OUT/yolov8s.hef" "$OUT/blistertrace.hef"
"$VENV/bin/python" - "$MODEL" "$OUT" <<'PY'
import hashlib,json,subprocess,sys
from pathlib import Path
source=Path(sys.argv[1]);out=Path(sys.argv[2]);hef=out/'blistertrace.hef'
import re
log=(out/'compilation.log').read_text(errors='replace')
entries=re.findall(r'Using dataset with (\d+) entries for calibration',log)
report={'architecture':'hailo8','classes':7,'source_onnx_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'hef_sha256':hashlib.sha256(hef.read_bytes()).hexdigest(),'hef_bytes':hef.stat().st_size,
        'model_zoo':'v2.19.1','compiler':'3.34.0','available_calibration_images':512,
        'actual_calibration_entries':int(entries[-1]) if entries else None,
        'cpu_only_optimization_level_zero':'Reducing optimization level to 0' in log,
        'int8_accuracy_verified':False,'target_inference_verified':False}
(out/'compile_receipt.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
PY
printf '\nCompiled HEF: %s/blistertrace.hef\n' "$OUT"
printf 'Next: target HailoRT load/inference and INT8 quality evaluation.\n'
