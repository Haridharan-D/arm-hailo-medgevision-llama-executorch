"""HailoRT adapter for a YOLOv8 HEF with FLOAT32 per-class NMS output.

Requires a custom seven-class Hailo-8 HEF. Hardware verification is mandatory.
API: HailoRT v4.20 VDevice/InferVStreams. No silent CPU fallback.
"""
from contextlib import ExitStack
from pathlib import Path
import numpy as np

class HailoDetector:
    def __init__(self,path):
        if not Path(path).is_file():raise FileNotFoundError(f'Custom HEF missing: {path}')
        from hailo_platform import (HEF,VDevice,ConfigureParams,HailoStreamInterface,
                                    InputVStreamParams,OutputVStreamParams,FormatType,InferVStreams)
        self.stack=ExitStack()
        try:
            self.hef=HEF(str(path));self.device=self.stack.enter_context(VDevice())
            params=ConfigureParams.create_from_hef(self.hef,interface=HailoStreamInterface.PCIe)
            self.group=self.device.configure(self.hef,params)[0]
            inputs=self.hef.get_input_vstream_infos();outputs=self.hef.get_output_vstream_infos()
            if len(inputs)!=1 or tuple(inputs[0].shape)!=(640,640,3):raise RuntimeError('HEF input must be 640x640 RGB')
            if len(outputs)!=1 or 'nms' not in outputs[0].name.lower():raise RuntimeError('HEF must expose one seven-class Hailo NMS output')
            self.input_name=inputs[0].name;self.output_name=outputs[0].name
            in_params=InputVStreamParams.make(self.group,quantized=True,format_type=FormatType.UINT8)
            out_params=OutputVStreamParams.make(self.group,quantized=False,format_type=FormatType.FLOAT32)
            self.stack.enter_context(self.group.activate(self.group.create_params()))
            self.pipeline=self.stack.enter_context(InferVStreams(self.group,in_params,out_params))
        except Exception:
            self.stack.close();raise

    def predict(self,rgb):
        if rgb.shape!=(640,640,3) or rgb.dtype!=np.uint8:raise ValueError('HEF input requires 640x640 uint8 RGB')
        outputs=self.pipeline.infer({self.input_name:np.ascontiguousarray(rgb)[None]})
        value=outputs[self.output_name][0]
        if len(value)!=7:raise RuntimeError('HEF NMS output class count must be seven')
        result=[]
        for cls,rows in enumerate(value):
            for row in rows:
                if len(row)!=5:raise RuntimeError('Unexpected Hailo NMS detection layout')
                y1,x1,y2,x2,score=map(float,row)
                if not np.isfinite([y1,x1,y2,x2,score]).all() or not 0<=score<=1:
                    raise RuntimeError('Invalid Hailo detection values')
                if score>0:result.append([x1*640,y1*640,x2*640,y2*640,score,cls])
        return result

    def close(self):self.stack.close()
