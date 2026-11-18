"""D25 diagnostic on the shipped model (crops edited, nothing trained): copy the gray line into the symbols channel left of the staff start, or erase the symbols channel there.
usage: PYTHONPATH=run/rel_wt python diag_symbols.py   (needs the *_crops.npz of run_all.py)"""
import numpy as np
from homr import staff_relations as sr
m = sr.get_model()
for names in (['schott_te5_p029', 'schott_te10_p076', 'schott_sonata_p02'], ['working_waldstein_p02', 'working_paganini_p11']):
    c = np.concatenate([np.load(f'{n}_crops.npz')['crops'] for n in names]).astype(np.float32)
    c2 = c.copy(); c2[:, 2, :, :44] = np.maximum(c[:, 2, :, :44], c[:, 0, :, :44])
    c3 = c.copy(); c3[:, 2, :, :44] = 0
    for lab, x in (('as is', c), ('symbols margin := max(symbols, gray ink)', c2), ('symbols margin erased', c3)):
        p = m.predict(x)
        print(names[0][:6], lab, 'grand calls', int((p.argmax(1) == 2).sum()), 'of', len(p), 'mean p(grand)', round(float(p[:, 2].mean()), 2), 'mean p(same)', round(float(p[:, 1].mean()), 2))
