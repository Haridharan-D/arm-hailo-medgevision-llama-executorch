"""Pinned publisher conversion of Meta SpinQuant; separate experimental artifacts.
This is MediaTek's PTE conversion, not a Meta-published executable. No re-quantization.
"""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path.home()/'BlisterTrace/Llama_ExecuTorch'))
import download_model as download
download.REPO='MediaTek-Research/Llama-3.2-3B-Instruct-SpinQuant_INT4_EO8-executorch'
download.REVISION='c2ac31ba586e93aad76b2f72aeaf0ecb7d061661'
download.FILES={'llama3_2-2048-spin.pte':('55d7f829f13063331c3d421816128553b545847628e1f0c71f44a78cb9229271',2553367552),
    'tokenizer.bin':('82e9d31979e92ab929cd544440f129d9ecd797b69e327f80f17e1c50d5551b55',2183982),
    'README.md':(None,423)}
out=Path.home()/'BlisterTrace/Llama_Candidates/3b_mediatek_2048'
download.download(out)
(out/'provenance.json').write_text(json.dumps({'repo':download.REPO,'revision':download.REVISION,'model':'Meta Llama3.2 3B Instruct SpinQuant INT4 EO8',
    'conversion_publisher':'MediaTek Research','experimental':True,'production_selected':False,'runtime_compatibility':'must be measured','export_recipe':'Publisher does not supply a reproducible export recipe in this repository; cannot prove all export flags.'},indent=2))
