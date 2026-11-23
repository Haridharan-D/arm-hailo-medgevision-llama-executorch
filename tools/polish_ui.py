"""Small source-only UI corrections; preserve saved design snapshots."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=root/'web/js/app.js';s=p.read_text(encoding='utf8')
old='Generating a bounded SOP action on the Arm CPU. This does not block inspections.</p>'
new=old+'<button class="btn small-btn ghost" data-action="cancel-advice">Cancel advisory</button>'
if new not in s:
    assert old in s;s=s.replace(old,new)
s=s.replace('Real QA authorization is not implemented by this UI.','This PIN changes display identity only; account permissions are enforced by the server.')
p.write_text(s,encoding='utf8')
classic=root/'web/js/classic.js';s=classic.read_text(encoding='utf8')
needle="document.addEventListener('keydown',e=>{if(!entered)"
s=s.replace(needle,"document.addEventListener('keydown',e=>{if(e.target.closest('dialog[open]'))return;if(!entered)")
classic.write_text(s,encoding='utf8')
print('Pending-advisory cancellation control and display-identity wording updated.')
