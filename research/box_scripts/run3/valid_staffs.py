"""Which staffs pass the training-time filters (data_loader._filter_valid_samples: sequence length, ledger lines) and
the vocabulary check, judged on the run-1 token files (they differ from the run-3 files only in the lift field).
usage: valid_staffs.py <set>  -> lists/valid_<set>.txt (image paths) ; run with PYTHONPATH=/workspace/homr_acc
"""
import multiprocessing as mp, re, sys
from homr.transformer.configs import Config
from training.transformer.data_loader import MAX_ALLOWED_LEDGER_LINES
from training.transformer.training_vocabulary import check_token_lines, max_ledger_lines, read_tokens

MAXLEN = Config().max_seq_len - 2


def ok(item):
    png, tok = item
    try:
        t = read_tokens(tok)
        check_token_lines(t)
    except Exception:
        return png, "vocab"
    if len(t) > MAXLEN:
        return png, "long"
    if max_ledger_lines(t) > MAX_ALLOWED_LEDGER_LINES:
        return png, "ledger"
    return png, "ok"


if __name__ == "__main__":
    name = sys.argv[1]
    items = [tuple(l.strip().split(",")) for l in open(f"/workspace/run3/lists/idx_{name}.txt")]
    import collections
    c = collections.Counter()
    with mp.Pool(50) as p, open(f"/workspace/run3/lists/valid_{name}.txt", "w") as fo:
        for png, r in p.imap(ok, items, chunksize=200):
            c[r] += 1
            if r == "ok":
                if name == "kern_scriabin":
                    m = re.search(r"-vrv-\d+-(\d+)\.png$", png)
                    if m and int(m[1]) >= 1:
                        c["scriabin vrv part>=1"] += 1
                        continue
                fo.write(png + "\n")
    print(name, dict(c))
