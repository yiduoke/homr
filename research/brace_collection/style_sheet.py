"""style_sheet.py OUT.png EDITION... : for every edition two page crops (left 30 %, upper half) at 150 dpi, to judge the brace by eye."""
import sys,glob,os
from PIL import Image,ImageDraw
out=sys.argv[1];rows=[]
for ed in sys.argv[2:]:
    fs=sorted(glob.glob(f'pages/{ed}/page-*.png'))
    pick=[fs[len(fs)//3],fs[(2*len(fs))//3]] if len(fs)>2 else fs
    tiles=[]
    for f in pick:
        im=Image.open(f).convert('L');w,h=im.size
        c=im.crop((0,int(h*0.06),int(w*0.30),int(h*0.52)))
        c=c.resize((340,int(c.height*340/c.width)))
        tiles.append(c)
    H=max(t.height for t in tiles)+14
    r=Image.new('L',(sum(t.width for t in tiles)+10,H),255);d=ImageDraw.Draw(r);d.text((2,0),ed,fill=0)
    x=0
    for t in tiles:r.paste(t,(x,14));x+=t.width+10
    rows.append(r)
# lay rows in 3 columns
cols=3;W=rows[0].width;rh=max(r.height for r in rows)
o=Image.new('L',(W*cols,rh*((len(rows)+cols-1)//cols)),255)
for i,r in enumerate(rows):o.paste(r,((i%cols)*W,(i//cols)*rh))
o.save(out);print(o.size)
