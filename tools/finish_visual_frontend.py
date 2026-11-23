"""Expose explicit selected demo labels in the preserved classic dashboard."""
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'web/js/classic.js';s=p.read_text(encoding='utf8')
s=s.replace("const rows=anomaly?await api.anomalySamples($('#profile').value):library;", "const rows=anomaly?await api.anomalySamples($('#profile').value):[...library].sort((a,b)=>Number(b.group?.startsWith('demo_'))-Number(a.group?.startsWith('demo_')));")
s=s.replace("esc(anomaly?r.case_id:'CASE-'+String(i+1).padStart(3,'0'))", "esc(anomaly?r.case_id:(r.display_name||r.name))")
p.write_text(s,encoding='utf8');print('Classic demo selection labels updated.')
