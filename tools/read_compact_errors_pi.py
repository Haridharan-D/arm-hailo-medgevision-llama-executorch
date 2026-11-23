import json,collections
from pathlib import Path
p=Path.home()/'BlisterTrace/releases/hardening_20261122/validation/hardening/20261122/quality_1b_compact_v2/cases.jsonl'
rows=[json.loads(l) for l in p.read_text().splitlines()]
print(collections.Counter(r.get('diagnostics',{}).get('fallback_detail') for r in rows))
for r in rows[:3]:print(r['case_id'],r.get('diagnostics',{}).get('raw_response'))
