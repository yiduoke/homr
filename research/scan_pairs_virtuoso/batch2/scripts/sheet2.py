"""Eye-review sheets: page region of the scan (with margin above, so brackets show) over the Verovio engraving of the label measures
(an 8va/8vb open at the window start is re-opened, one open at the end closed). 
usage: sheet2.py <outdir> <name> ...   (names = crop names; reads work/export/*.json)  env SHEET_W (default 1500), SHEET_PAD_TOP (default 70)"""
import sys, os, json, glob, copy, zipfile, tempfile, subprocess
import xml.etree.ElementTree as ET
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verovio; verovio.enableLog(verovio.LOG_OFF)
from PIL import Image, ImageDraw
from pieces2 import BY
B = '/Users/yiduoke/Documents/homr/run/scan_pairs_virtuoso/batch2/'
ASAP = '/Users/yiduoke/Documents/homr/run/box_scripts/r6_extra/asap_mxl/'
recs = {}
for f in glob.glob(B + 'work/export/*.json'):
    for r in json.load(open(f))['records']:
        if r.get('name'): recs[r['name']] = r

def xml_window(asap, a, b):
    import labels2
    root = ET.fromstring(labels2.xml_text(asap).encode())
    part = root.find('part'); meas = part.findall('measure')
    state = {}; open_ = {}
    for m in meas[:a]:
        for at in m.findall('attributes'):
            for ch in at: state[ch.tag + (ch.get('number') or '')] = ch
        for d in m.findall('direction'):
            for o in d.iter('octave-shift'):
                k = (o.get('number'), d.findtext('staff'))
                if o.get('type') in ('up', 'down'): open_[k] = copy.deepcopy(d)
                elif o.get('type') == 'stop': open_.pop(k, None)
    for m in meas: part.remove(m)
    first = True
    for m in meas[a:b]:
        m = copy.deepcopy(m)
        for p in m.findall('print'): m.remove(p)
        if first:
            if state:
                at = ET.Element('attributes')
                for tag in ["divisions", "key", "time", "staves", "clef"]:
                    for key, ch in state.items():
                        if ch.tag == tag: at.append(copy.deepcopy(ch))
                m.insert(0, at)
            for k, d in open_.items():
                for o in d.iter('octave-shift'): o.attrib.pop('default-y', None)
                m.insert(1 if state else 0, d)
        first = False; part.append(m)
    st = {}
    for m in part.findall('measure'):
        for d in m.findall('direction'):
            for o in d.iter('octave-shift'):
                k = (o.get('number'), d.findtext('staff'))
                if o.get('type') in ('up', 'down'): st[k] = d
                elif o.get('type') == 'stop': st.pop(k, None)
    lastm = part.findall('measure')[-1]
    for k, d in st.items():
        nd = copy.deepcopy(d)
        for o in nd.iter('octave-shift'):
            o.set('type', 'stop'); o.attrib.pop('default-y', None)
        lastm.append(nd)
    return ET.tostring(root, encoding='unicode')

def render_label(asap, a, b, out, width):
    tk = verovio.toolkit()
    tk.setOptions({"pageWidth": width, "scale": 45, "adjustPageHeight": True, "breaks": "none", "pageMarginTop": 20, "pageMarginBottom": 20,
                   "pageMarginLeft": 20, "pageMarginRight": 20, "header": "none", "footer": "none"})
    tk.loadData(xml_window(asap, a, b))
    tmp = tempfile.mktemp(suffix='.svg'); open(tmp, 'w').write(tk.renderToSVG(1))
    subprocess.run(['rsvg-convert', '-b', 'white', '-w', str(width), '-o', out, tmp], check=True); os.remove(tmp)

def make(name, out, W=None, pad_top=None, pad_bot=25, extra=''):
    W = W or int(os.environ.get('SHEET_W', 1500)); pad_top = pad_top if pad_top is not None else int(os.environ.get('SHEET_PAD_TOP', 70))
    r = recs[name]; cfg = BY[r['pid']]
    page = Image.open(B + f"work/pages/{r['pdf']}/{r['page']}.png").convert('L')
    x0, y0, x1, y1 = r['bbox']
    reg = page.crop((max(0, x0 - 15), max(0, y0 - pad_top), min(page.width, x1 + 15), min(page.height, y1 + pad_bot)))
    reg = reg.resize((W, int(reg.height * W / reg.width)))
    a, b = r['measures']; lab = tempfile.mktemp(suffix='.png')
    render_label(cfg['asap'], a, b, lab, W); L = Image.open(lab).convert('L'); os.remove(lab)
    H = reg.height + L.height + 44
    sheet = Image.new('L', (W, H), 255); y = 0
    for t, im in (('scan', reg), ('label measures (Verovio)', L)):
        d = ImageDraw.Draw(sheet); d.rectangle((0, y, W, y + 20), fill=0)
        d.text((6, y + 4), f"{name} {cfg['title']} idx {a}-{b-1} L={b-a} | {t} {extra}", fill=255); y += 22
        sheet.paste(im, (0, y)); y += im.height
    sheet.save(out)

if __name__ == '__main__':
    os.makedirs(sys.argv[1], exist_ok=True)
    for n in sys.argv[2:]: make(n, os.path.join(sys.argv[1], n + '.png'))
