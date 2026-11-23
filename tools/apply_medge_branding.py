"""Rename visible product labels, retaining stable paths and stored evidence."""
from pathlib import Path
root=Path(__file__).resolve().parents[1];changed=[]
for p in (root/'web').rglob('*.html'):
    if 'design-a' in p.parts:continue
    original=p.read_text(encoding='utf8');text=original.replace('BlisterTrace','Medge Vision')
    if p.name=='display.html':text=text.replace('MEDGE <span>SoC</span>','Medge<span> Vision</span>')
    if text!=original:p.write_text(text,encoding='utf8');changed.append(str(p.relative_to(root)))
replacements={
 'web/js/app.js':{'BlisterTrace<span':'Medge Vision<span','BlisterTrace home':'Medge Vision home',"+' · BlisterTrace'":"+' · Medge Vision'"},
 'web/js/intro.js':{'MEDGE SoC welcome':'Medge Vision welcome'},
 'web/js/display.js':{'BlisterTrace · live inspection status':'Medge Vision · live inspection status'},
 'main.py':{"description='BlisterTrace offline inspection'":"description='Medge Vision offline inspection'",'BlisterTrace startup failed':'Medge Vision startup failed','BlisterTrace startup error':'Medge Vision startup error'},
 'app/server.py':{"title='BlisterTrace'":"title='Medge Vision'","'application':'BlisterTrace','version':VERSION":"'application':'BlisterTrace','product_name':'Medge Vision','version':VERSION"},
 'app/pdf_report.py':{'BlisterTrace':'Medge Vision'},
 'deploy/blistertrace.service':{'Description=BlisterTrace':'Description=Medge Vision'},
}
for name,rules in replacements.items():
    p=root/name;original=p.read_text(encoding='utf8');text=original
    for before,after in rules.items():text=text.replace(before,after)
    if text!=original:p.write_text(text,encoding='utf8');changed.append(name)
print('Updated visible branding:',', '.join(changed));print('Stable service/model/database paths and historical evidence retained.')
