"""Small ASCII PDF writer for local batch evidence; no external PDF runtime."""
import textwrap
def batch_pdf(batch,rows,head):
    lines=['MEDGE VISION | BATCH INSPECTION REPORT','DRAFT - not a pharmaceutical release authorization','']
    for k in ['batch_id','sku','description','category','operator','started_at','ended_at','status','counts','defect_distribution','mean_detector_ms']:lines+=textwrap.wrap(k+': '+str(batch.get(k)),95)
    lines+=['Audit head: '+head,'','Inspection ID | Timestamp | Immutable decision']
    lines += [r['inspection_id']+' | '+r['created_at'][:19]+' | '+r['decision'] for r in rows]
    pages=[lines[i:i+47] for i in range(0,len(lines),47)];objects=[b'',b'',b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>'];kids=[]
    def escape(x):return x.replace('\\','\\\\').replace('(','\\(').replace(')','\\)').encode('ascii','replace')
    for page in pages:
        content=b'BT /F1 10 Tf 40 800 Td 15 TL '+b' '.join(b'('+escape(line)+b') Tj T*' for line in page)+b' ET'
        stream_id=len(objects)+1;objects.append(b'<< /Length '+str(len(content)).encode()+b' >>\nstream\n'+content+b'\nendstream')
        page_id=len(objects)+1;objects.append(f'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 3 0 R >> >> /Contents {stream_id} 0 R >>'.encode());kids.append(f'{page_id} 0 R')
    objects[0]=b'<< /Type /Catalog /Pages 2 0 R >>';objects[1]=('<< /Type /Pages /Kids ['+' '.join(kids)+f'] /Count {len(kids)} >>').encode()
    out=b'%PDF-1.4\n';offsets=[0]
    for i,obj in enumerate(objects,1):offsets.append(len(out));out+=f'{i} 0 obj\n'.encode()+obj+b'\nendobj\n'
    xref=len(out);out+=f'xref\n0 {len(offsets)}\n0000000000 65535 f \n'.encode()
    out+=b''.join(f'{o:010} 00000 n \n'.encode() for o in offsets[1:]);out+=f'trailer << /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF'.encode();return out
