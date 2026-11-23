"""Standalone engineering diagrams for the submission; no UI runtime libraries."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
out=Path(__file__).resolve().parents[2]/'BlisterTrace_Deliverables/Hardening_20261122/figures';out.mkdir(parents=True,exist_ok=True)
diagrams={
 'system_architecture':[['Upload / local image / USB','Frozen YOLOv8s · HailoRT / Hailo-8','Immutable deterministic finding','SQLite / source hashes / batch evidence'],['Selected inspection + demo SOP','Bounded asynchronous queue','Llama · ExecuTorch / Arm CPU','Validated advice or explicit fallback']],
 'vision_execution':[['Input image / fresh USB frame','RGB640 letterbox','Frozen Hailo-8 HEF','Frozen thresholds / NMS','HOLD / REVIEW / PASS']],
 'llama_execution':[['Immutable inspection evidence','Relevant local SOP clauses','Persistent native1B worker','JSON + claim checks','Advisory / draft · QA authority']],
 'traceability':[['Unique inspection / source SHA-256','Batch / model / config identity','Transactional SQLite WAL','Append-only QA + advisory events','SHA-256 chain / verified backup']],
 'inspection_workflow':[['Select open batch','Choose image / fresh USB snapshot','Immediate rule-engine result','Asynchronous advisory','Human QA note / report export']]}
for name,lanes in diagrams.items():
 fig,ax=plt.subplots(figsize=(14,2.7*len(lanes)),layout='constrained');ax.set_xlim(0,14);ax.set_ylim(0,len(lanes)*3);ax.axis('off')
 for j,lane in enumerate(lanes):
  width=13/len(lane);y=(len(lanes)-j-1)*3+.8
  for i,text in enumerate(lane):
   x=.4+i*width;box=FancyBboxPatch((x,y),width-.25,1.3,boxstyle='round,pad=0.08',facecolor='#edf8fa' if j==0 else '#f4effb',edgecolor='#167f90' if j==0 else '#8161ad',linewidth=1.5);ax.add_patch(box)
   words=text.split();mid=max(1,len(words)//2);label=' '.join(words[:mid])+'\n'+' '.join(words[mid:]);ax.text(x+(width-.25)/2,y+.65,label,ha='center',va='center',fontsize=10,color='#17283b')
   if i<len(lane)-1:ax.annotate('',xy=(x+width-.04,y+.65),xytext=(x+width-.22,y+.65),arrowprops={'arrowstyle':'->','color':'#526a7f'})
 ax.set_title(name.replace('_',' ').title()+' · BlisterTrace offline inspection',loc='left',fontsize=15,color='#17283b')
 fig.savefig(out/(name+'.png'),dpi=170);fig.savefig(out/(name+'.svg'));plt.close(fig)
print(out)
