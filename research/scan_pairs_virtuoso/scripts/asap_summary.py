import zipfile, sys, glob, os, xml.etree.ElementTree as ET
D="/Users/yiduoke/Documents/homr/run/box_scripts/r6_extra/asap_mxl/"
names="""Liszt_Transcendental_Etudes_1 Liszt_Transcendental_Etudes_9 Liszt_Transcendental_Etudes_11 Liszt_Ballade_2 Chopin_Etudes_op_10_1 Chopin_Etudes_op_25_1 Chopin_Etudes_op_25_2 Chopin_Etudes_op_25_5 Chopin_Etudes_op_25_12 Chopin_Ballades_1 Chopin_Ballades_3 Chopin_Barcarolle Chopin_Scherzos_31 Chopin_Sonata_3_4th Beethoven_Piano_Sonatas_32-1 Beethoven_Piano_Sonatas_31-3_4 Beethoven_Piano_Sonatas_14-3 Schumann_Kreisleriana_3 Schubert_Impromptu_op_90_D_899_1 Chopin_Etudes_op_10_12 Chopin_Ballades_2 Chopin_Sonata_2_4th Beethoven_Piano_Sonatas_17-3 Liszt_Transcendental_Etudes_3 Chopin_Sonata_2_2nd Schubert_Impromptu_op_90_D_899_2""".split()
for n in names:
    z=zipfile.ZipFile(D+n+".mxl"); x=z.read("score.xml")
    r=ET.fromstring(x)
    parts=r.findall("part")
    p=parts[0]; ms=p.findall("measure")
    rep=[(m.get("number"),b.find("repeat").get("direction")) for m in ms for b in m.findall("barline") if b.find("repeat") is not None]
    vol=[(m.get("number"),e.get("number"),e.get("type")) for m in ms for b in m.findall("barline") for e in b.findall("ending")]
    nums=[m.get("number") for m in ms]
    ts=[(m.get("number"),a.find("time/beats").text+"/"+a.find("time/beat-type").text) for m in ms for a in m.findall("attributes") if a.find("time/beats") is not None]
    mmr=sum(1 for m in ms for a in m.findall("attributes") if a.find("measure-style/multiple-rest") is not None)
    nn=sum(1 for m in ms for nt in m.findall("note") if nt.find("rest") is None)
    print(n, "parts",len(parts),"meas",len(ms),"last",nums[-1],"notes",nn,"rep",rep[:8],"endings",vol[:6],"ts",ts[:6],"mmr",mmr)
