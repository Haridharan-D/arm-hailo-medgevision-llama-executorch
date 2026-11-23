"""Export the three audited EfficientAD-S checkpoints to CPU ONNX with real heatmap outputs."""
from pathlib import Path
import hashlib,io,json,sys,time,zipfile
import numpy as np
import torch
import torch.nn.functional as F
import onnxruntime as ort
ROOT=Path(__file__).resolve().parent
OUT=ROOT.parent/'BlisterTrace_App/models/anomaly'
SRC=ROOT/'deployment_src/auditnet';SRC.mkdir(parents=True,exist_ok=True)
audit=json.loads((ROOT/'MODEL_AUDIT.json').read_text())
with zipfile.ZipFile(ROOT/audit['models'][0]['archive']) as z:
    for name in ['network.py','upstream_reference.py']:(SRC/name).write_bytes(z.read('models/02_efficientad/models/'+name))
(SRC/'__init__.py').write_text('')
sys.path.insert(0,str(SRC.parent))
from auditnet.network import EfficientAD,raw_maps
torch.set_num_threads(2)

class Deployment(torch.nn.Module):
    def __init__(self,model,normalization):
        super().__init__();self.model=model
        self.register_buffer('mean',torch.tensor([.485,.456,.406]).view(1,3,1,1))
        self.register_buffer('std',torch.tensor([.229,.224,.225]).view(1,3,1,1))
        self.register_buffer('lo',torch.tensor(normalization['start']).view(1,2,1,1))
        self.register_buffer('hi',torch.tensor(normalization['end']).view(1,2,1,1))
    def forward(self,image):
        raw=raw_maps(self.model((image-self.mean)/self.std))
        fused=(.1*(raw-self.lo)/(self.hi-self.lo).clamp_min(1e-6)).mean(1,keepdim=True)
        heatmap=F.interpolate(F.pad(fused,(4,4,4,4)),size=(256,256),mode='bilinear',align_corners=False)
        return heatmap,heatmap.flatten(1).amax(1)

results=[]
for entry in audit['models']:
    profile=entry['run'];folder=OUT/profile;folder.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(ROOT/entry['archive']) as z:
        contract=json.loads(z.read('model_contract.json'))
        ckpt=torch.load(io.BytesIO(z.read('runs/'+profile+'/best.pt')),map_location='cpu',weights_only=True)
        model=EfficientAD((256,256)).eval();model.load_state_dict(ckpt['model'],strict=True)
        deployed=Deployment(model,ckpt['normalization']).eval()
        x=torch.rand((1,3,256,256),generator=torch.Generator().manual_seed(42))
        target=folder/'model.onnx'
        torch.onnx.export(deployed,x,str(target),opset_version=17,dynamo=False,
            input_names=['image'],output_names=['heatmap','score'],do_constant_folding=True)
        options=ort.SessionOptions();options.intra_op_num_threads=2;options.inter_op_num_threads=1
        session=ort.InferenceSession(str(target),sess_options=options,providers=['CPUExecutionProvider'])
        with torch.inference_mode():expected=[t.numpy() for t in deployed(x)]
        actual=session.run(None,{'image':x.numpy()})
        deltas=[float(np.max(np.abs(a-b))) for a,b in zip(actual,expected)]
        assert all(np.allclose(a,b,atol=1e-4,rtol=1e-4) for a,b in zip(actual,expected)),deltas
        contract.update(profile=profile,artifact='model.onnx',artifact_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
            deployment_input={'shape':[1,3,256,256],'dtype':'float32','color':'RGB','range':[0,1],
            'resize':'Pillow bilinear; ImageNet normalization is inside ONNX'},
            deployment_output={'heatmap':[1,1,256,256],'score':[1]},
            onnx_parity={'passed':True,'random_seed':42,'max_abs_differences':deltas},
            validated_for_local_camera=False,
            quality_warning='Low VisA image recall at saved threshold; benchmark/research only' if profile=='visa_capsules' else 'Category benchmark; local-camera/product validation required',
            license='CC BY 4.0 dataset' if profile=='visa_capsules' else 'MVTec AD CC BY-NC-SA 4.0 dataset; non-commercial research',
            architecture_source='EfficientAD PDN-S teacher/student/autoencoder; source provenance retained in audited Submission archive')
        (folder/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
        results.append({'profile':profile,'path':str(target),'bytes':target.stat().st_size,'parity':contract['onnx_parity']})
        print(json.dumps(results[-1]),flush=True)
(OUT/'export_report.json').write_text(json.dumps(results,indent=2))
