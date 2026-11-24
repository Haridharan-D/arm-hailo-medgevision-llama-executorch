import sys,json,hashlib
from pathlib import Path
ROOT=Path.home()/"BlisterTrace/releases/hardening_20261122"
sys.path.insert(0,str(ROOT))
from tools import medge_demo as demo
CASES=[("YOLO","yolo","acceptance_demo/safe/safe_01.jpg","acceptance_demo/defective/crack/crack.jpg"),("MVTec pill","mvtec_pill","demo/safe/safe_01.png","demo/defective/defective_01.png"),("MVTec capsule","mvtec_capsule","demo/safe/safe_01.png","demo/defective/defective_01.png"),("VisA capsules","visa_capsules","demo/safe/safe_01.png","demo/defective/defective_01.png")]
def check():
 for title,profile,clear,defect in CASES:
  for image in [clear,defect]:
   base=ROOT/"test_images" if profile=="yolo" else ROOT/"models/anomaly/samples"/profile
   path=base/image
   if not path.is_file():raise RuntimeError("Missing test image: "+str(path))
   if profile!="yolo":
    row=next(x for x in json.loads((base/"manifest.json").read_text()) if x["file"]==image)
    if hashlib.sha256(path.read_bytes()).hexdigest()!=row["sha256"]:raise RuntimeError("Sample checksum mismatch")
 print("All eight selected test images verified.",flush=True)
def main():
 check()
 if "--check" in sys.argv:return
 demo.start();demo.models()
 matches=[]
 for i,(title,profile,clear,defect) in enumerate(CASES,1):
  for j,(image,expected) in enumerate([(clear,"SAFE"),(defect,"DEFECTIVE")],1):
   key=f"{i}-{j}"
   demo.CASES[key]=(title+" selected "+expected,profile,image,expected)
   try:
    matches.append(demo.run_case(key,timeout=180))
    _,session=demo.state()
    row=json.loads(Path(session["records"][-1]["file"]).read_text())
    print("\nFULL ADVISORY / SOP / QA DRAFT",flush=True)
    print(json.dumps(row.get("advice"),indent=2),flush=True)
   except Exception as error:
    matches.append(False);print("TEST ERROR:",type(error).__name__,str(error),flush=True)
 demo.summary()
 print(f"\nSelected demo matches: {sum(matches)}/8. Not an accuracy benchmark.",flush=True)
 print("Fallback or reused advice is explicitly identified; only llama_validated is validated model output.",flush=True)
 print("Dashboard command: ~/medge-vision",flush=True)
 if not all(matches):raise SystemExit(2)
if __name__=="__main__":main()
