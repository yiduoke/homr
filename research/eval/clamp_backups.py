"""Clamp <backup> durations that reach before the start of a bar (malformed ASAP bars). Usage: IN OUT"""
import sys
from xml.etree import ElementTree as ET
t=ET.parse(sys.argv[1]); r=t.getroot(); n=0
for part in r.findall('part'):
    for m in part.findall('measure'):
        cur=0; last=None
        for e in m:
            if e.tag=='backup':
                d=int(e.findtext('duration'))
                if d>cur: e.find('duration').text=str(cur); n+=1; d=cur
                cur-=d
            elif e.tag=='forward': cur+=int(e.findtext('duration'))
            elif e.tag=='note' and e.find('chord') is None and e.find('grace') is None: cur+=int(e.findtext('duration') or 0)
print('clamped',n,file=sys.stderr); t.write(sys.argv[2])
