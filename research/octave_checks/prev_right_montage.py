import sys,json
sys.path.insert(0,'/Users/yiduoke/Documents/homr/run/octave_checks')
import octave_causes_crops as O
from PIL import Image, ImageDraw
crops=O.load_all()
idx={}
for i,c in enumerate(crops): idx.setdefault((c['set'],c['row']['pid']),[]).append(c)
byn={c['name']:c for c in crops}
names=sys.argv[2:]
tiles=[]
for n in names:
    c=byn[n]; lst=idx[(c['set'],c['row']['pid'])]; k=[x['name'] for x in lst].index(n); p=lst[k-1]
    row=p['row']; page=Image.open(p['base']+row['page_image']).convert('L')
    x0,y0,x1,y1=map(int,row['page_bbox_xyxy'].split())
    reg=page.crop((max(0,x1-700),max(0,y0-80),x1+10,min(page.height,y1+20)))
    d=Image.new('RGB',(reg.width,reg.height+16),'white'); d.paste(reg.convert('RGB'),(0,16))
    ImageDraw.Draw(d).text((4,2),f"previous system of {n}: {p['name']} meas {row['asap_measure_range']} (right end)",fill=(200,0,0))
    tiles.append(d)
W=max(t.width for t in tiles); H=sum(t.height for t in tiles)
m=Image.new('RGB',(W,H),'white'); y=0
for t in tiles: m.paste(t,(0,y)); y+=t.height
m.save(sys.argv[1])
