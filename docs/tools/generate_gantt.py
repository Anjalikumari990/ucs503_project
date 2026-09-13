"""Generate editable SVG diagrams and an Excel Gantt workbook with Python's standard library."""
from pathlib import Path
from html import escape
import csv
import zipfile

DOCS = Path(__file__).resolve().parents[1]
NAVY, GREEN, BLUE, GRAY = '#17324d', '#158575', '#3975b8', '#63758a'

def text(x,y,lines,size=16,color=NAVY,anchor='middle'):
    if isinstance(lines,str): lines=[lines]
    return ''.join(f'<text x="{x}" y="{y+i*(size+6)}" font-family="Arial, sans-serif" font-size="{size}" fill="{color}" text-anchor="{anchor}">{escape(line)}</text>' for i,line in enumerate(lines))
def rect(x,y,w,h,fill='#fff',stroke=NAVY,rx=0):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>'
def arrow(points,label='',lx=0,ly=0):
    return f'<polyline points="{points}" fill="none" stroke="{GRAY}" stroke-width="2" marker-end="url(#arrow)"/>'+ (text(lx,ly,label,12) if label else '')
def svg(w,h,body,title):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title"><title id="title">{escape(title)}</title><defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="{GRAY}"/></marker></defs><rect width="100%" height="100%" fill="#fff"/>{body}</svg>'''

# Relative weeks: indicative activity allocation, not invented calendar dates.
tasks=[
('T01','Requirements and project scope',1,1,'Completed','—'),
('T02','Proposal and system design',1,2,'Completed','T01'),
('T03','Keyboard event collector',1,1,'Completed','T01'),
('T04','HMAC identifiers and protected storage',1,1,'Completed','T03'),
('T05','Hold / flight timing extraction',1,1,'Completed','T04'),
('T06','10-second windows and activity flag',1,1,'Completed','T05'),
('T07','Level 0 / Level 1 and use-case diagrams',2,2,'Completed','T02'),
('T08','Project presentation',2,2,'Completed','T02'),
('T09','Isolation Forest pipeline',3,3,'Completed','T06'),
('T10','Trust mapping and decision engine',3,3,'Completed','T09'),
('T11','Flask dashboard and live capture',3,3,'Completed','T10'),
('T12','Replay and integration checks',3,3,'Completed','T11'),
('T13','Revised proposal, Level 2 DFD and schedule',3,3,'Completed','T07,T10'),
('T14','Additional users and recording sessions',4,4,'Planned','T12'),
('T15','Feature quality and held-out session split',4,4,'Planned','T14'),
('T16','Retrain and evaluate baseline',5,5,'Planned','T15'),
('T17','Takeover trials and threshold review',5,5,'Planned','T16'),
('T18','Latency and false-accept / reject report',5,6,'Planned','T17'),
('T19','Final report and slide update',6,6,'Planned','T18'),
('T20','Demo rehearsal and submission preparation',6,6,'Planned','T19'),
]
with (DOCS/'planning/gantt_tasks.csv').open('w',newline='') as f:
    writer=csv.writer(f, lineterminator="\n");writer.writerow(['ID','Task','Start week','End week','Status','Dependencies']);writer.writerows(tasks)
b=text(750,45,'ADAPTIVE CONTINUOUS AUTHENTICATION',27)+text(750,81,'PROJECT GANTT CHART • Six-week milestone plan',21)
b+=text(35,118,'Relative weeks; retrospective allocation is indicative. Weeks 4–6 are planned, with no fixed submission date assumed.',15,anchor='start')
for c in range(6): b+=text(740+c*125,166,f'WEEK {c+1}',16)
for r,(id_,name,start,end,status,deps) in enumerate(tasks):
    y=187+r*38
    b+=rect(25,y,1450,38,'#f3f6fa' if r%2==0 else '#fff','#e3e9ef')+text(38,y+25,id_,14,anchor='start')+text(95,y+25,name,15,anchor='start')
    for week in range(1,7):
        if start<=week<=end:b+=rect(686+(week-1)*125,y+7,108,24,GREEN if status=='Completed' else BLUE,'none',5)
b+=text(35,990,'GREEN: completed repository milestone     BLUE: planned work',17,anchor='start')
b+=text(35,1022,'Dependencies, status notes and editable week cells are included in the Excel workbook and CSV.',15,anchor='start')
(DOCS/'planning/Gantt_Chart.svg').write_text(svg(1500,1060,b,'Project Gantt chart — Adaptive Continuous Authentication'))

# Portable OOXML workbook: no third-party packages required. Formula cells recalculate after editing weeks.
ns='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
def cell(col,row,value,style=0,formula=False):
    address=f'{col}{row}'
    if formula:return f'<c r="{address}" s="{style}"><f>{escape(value)}</f><v>0</v></c>'
    if isinstance(value,int):return f'<c r="{address}" s="{style}"><v>{value}</v></c>'
    return f'<c r="{address}" s="{style}" t="inlineStr"><is><t>{escape(str(value))}</t></is></c>'
def row(n,values):return f'<row r="{n}">'+''.join(cell(chr(65+i),n,v) for i,v in enumerate(values))+'</row>'
rows=[row(1,['Adaptive Continuous Authentication — Gantt Chart']),row(2,['Edit Start / End week (1–6); timeline bars recalculate in Excel.']),row(3,['Weeks 1–3 are indicative retrospective allocations; Weeks 4–6 are plans.']),row(5,['ID','Task','Start week','End week','Status','Dependencies',1,2,3,4,5,6])]
for n,t in enumerate(tasks,6):
    cells=''.join(cell(chr(65+i),n,v) for i,v in enumerate(t))
    for i in range(6):
        col=chr(71+i); cells+=cell(col,n,f'IF(AND({col}$5>=$C{n},{col}$5<=$D{n}),IF($E{n}="Completed",1,2),0)',1,True)
    for i in range(6):
        col=chr(71+i)
        cached=(1 if t[4]=='Completed' else 2) if t[2]<=i+1<=t[3] else 0
        import re
        cells=re.sub(r'(<c r="'+col+str(n)+r'"[^>]*><f>.*?</f><v>)0(</v>)',lambda m:m[1]+str(cached)+m[2],cells)
    rows.append(f'<row r="{n}" ht="25" customHeight="1">{cells}</row>')
sheet=f'''<worksheet xmlns="{ns}"><sheetViews><sheetView workbookViewId="0"><pane xSplit="2" ySplit="5" topLeftCell="C6" activePane="bottomRight" state="frozen"/></sheetView></sheetViews><cols><col min="1" max="1" width="8" customWidth="1"/><col min="2" max="2" width="57" customWidth="1"/><col min="3" max="4" width="12" customWidth="1"/><col min="5" max="6" width="19" customWidth="1"/><col min="7" max="12" width="10" customWidth="1"/></cols><sheetData>{''.join(rows)}</sheetData><autoFilter ref="A5:L25"/><conditionalFormatting sqref="G6:L25"><cfRule type="cellIs" dxfId="0" priority="1" operator="equal"><formula>1</formula></cfRule><cfRule type="cellIs" dxfId="1" priority="2" operator="equal"><formula>2</formula></cfRule></conditionalFormatting><dataValidations count="1"><dataValidation type="whole" operator="between" allowBlank="0" showErrorMessage="1" sqref="C6:D25"><formula1>1</formula1><formula2>6</formula2></dataValidation></dataValidations><pageSetup orientation="landscape" paperSize="8" fitToWidth="1" fitToHeight="1"/></worksheet>'''
notes=[['Schedule notes'],['Scope','Keyboard-only course prototype; no new model performance is claimed.'],['Week basis','Six relative weeks follow the journal sequence; calendar dates are not assumed.'],['Completed','Existing artifact or implementation is present; week allocation is indicative.'],['Planned','Future work; replace with actual dates/status as it happens.'],['Dependencies','Task IDs are sequencing guidance; same-week tasks may occur sequentially.'],['Reference','https://github.com/NamanArora2709/ucs503p-202627-privalens'],['Reference access','Repository lists a Gantt workbook; individual file could not be retrieved.'],['Legend','Green = completed; blue = planned.'],['Editing','Change columns C/D and status Completed or Planned; formula cells recalculate.'],['Preview','Regenerate SVG/CSV/workbook from docs/tools/generate_planning_assets.py; generation overwrites workbook edits.']]
notesxml=f'<worksheet xmlns="{ns}"><cols><col min="1" max="1" width="20" customWidth="1"/><col min="2" max="2" width="115" customWidth="1"/></cols><sheetData>'+''.join(row(i,v) for i,v in enumerate(notes,1))+'</sheetData></worksheet>'
styles=f'''<styleSheet xmlns="{ns}"><numFmts count="1"><numFmt numFmtId="164" formatCode=";;;"/></numFmts><fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts><fills count="2"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill></fills><borders count="1"><border/></borders><cellStyleXfs count="1"><xf/></cellStyleXfs><cellXfs count="2"><xf fontId="0" fillId="0" borderId="0" xfId="0"/><xf numFmtId="164" applyNumberFormat="1" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs><cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles><dxfs count="2"><dxf><fill><patternFill patternType="solid"><fgColor rgb="FF158575"/><bgColor indexed="64"/></patternFill></fill></dxf><dxf><fill><patternFill patternType="solid"><fgColor rgb="FF3975B8"/><bgColor indexed="64"/></patternFill></fill></dxf></dxfs></styleSheet>'''
relsns='http://schemas.openxmlformats.org/package/2006/relationships'; officens='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
files={
'[Content_Types].xml':'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/><Override PartName="/xl/worksheets/sheet2.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/></Types>',
'_rels/.rels':f'<Relationships xmlns="{relsns}"><Relationship Id="rId1" Type="{officens}/officeDocument" Target="xl/workbook.xml"/></Relationships>',
'xl/workbook.xml':f'<workbook xmlns="{ns}" xmlns:r="{officens}"><sheets><sheet name="Gantt Chart" sheetId="1" r:id="rId1"/><sheet name="Notes" sheetId="2" r:id="rId2"/></sheets><calcPr calcId="0" fullCalcOnLoad="1"/></workbook>',
'xl/_rels/workbook.xml.rels':f'<Relationships xmlns="{relsns}"><Relationship Id="rId1" Type="{officens}/worksheet" Target="worksheets/sheet1.xml"/><Relationship Id="rId2" Type="{officens}/worksheet" Target="worksheets/sheet2.xml"/><Relationship Id="rId3" Type="{officens}/styles" Target="styles.xml"/></Relationships>',
'xl/worksheets/sheet1.xml':sheet,'xl/worksheets/sheet2.xml':notesxml,'xl/styles.xml':styles}
with zipfile.ZipFile(DOCS/'planning/Adaptive_Continuous_Authentication_Gantt.xlsx','w',zipfile.ZIP_DEFLATED) as z:
    for name,data in files.items():z.writestr(name,'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'+data)
print('Generated Gantt SVG, Excel workbook and task CSV.')
if __name__=='__main__':
    import xml.etree.ElementTree as ET
    for data in files.values():ET.fromstring(data)
    for name in ['planning/Gantt_Chart.svg']:ET.parse(DOCS/name)
    assert all(1<=t[2]<=t[3]<=6 for t in tasks)
    print('XML and schedule bounds validated.')
