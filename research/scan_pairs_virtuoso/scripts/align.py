"""Align the detected systems of a piece with the measures of its ASAP score (Viterbi over cumulative measure counts).
Score of giving system i the measures [s, s+L): 3*pitch-F1(model read, label notes) - bar-count penalty (barline counter);
a 'gap' (undetected system / edition difference) skips g label measures at a cost. Returns per-system (start, L, gap_before)."""
import collections, math

def f1(a: collections.Counter, b: collections.Counter):
    tp = sum((a & b).values())
    if not a and not b: return 1.0
    if tp == 0: return 0.0
    p = tp / max(1, sum(b.values())); r = tp / max(1, sum(a.values()))
    return 2 * p * r / (p + r)

def bar_k(groups_n, first_x, unit):
    """Number of measures the barline counter sees (None if undetermined). groups = k+1 with the joining line at the left edge."""
    if groups_n is None: return None
    if first_x is not None and unit and first_x <= 4 * unit: return groups_n - 1
    return groups_n

def align(systems, meas_notes, gap_cost=5.0, max_gap=30, start_range=0, end_free=True):
    """systems: list of dict(k (counter measures or None), model_notes (list of pitches or None), model_bars).
    meas_notes: list of Counter per label measure. Returns (assignments, total score, end)."""
    S, M = len(systems), len(meas_notes)
    prefix = [collections.Counter()]
    NEG = -1e9
    # candidate lengths per system
    def lens(sy):
        k = sy["k"]
        if k is None or k <= 0: return list(range(1, 25))
        return sorted({l for l in range(max(1, k - 2), k + 3)})
    cache = {}
    def scores_at(i, s):
        """scores of all candidate lengths L for system i starting at measure s (incremental sums, memoised):
        4 * bar-by-bar similarity + 1 * multiset pitch F1 - bar-count penalty"""
        key = (i, s)
        if key in cache: return cache[key]
        sy = systems[i]; res = {}
        want = set(lens(sy)); c = collections.Counter(); run = 0.0
        mb = sy.get("model_bars")
        for L in range(1, max(want) + 1):
            if s + L > M: break
            c.update(meas_notes[s + L - 1])
            if mb is not None and L <= len(mb): run += f1(meas_notes[s + L - 1], mb[L - 1])
            if L not in want: continue
            sc = 0.0
            if sy["model_notes"] is not None:
                sc += f1(c, sy["pitch_counter"])
                if mb is not None: sc += 4 * run / max(L, len(mb))
            k = sy["k"]
            if k is not None:
                d = abs(L - k); sc -= 0 if d == 0 else (2.0 if d == 1 else 5.0)
            res[L] = sc
        cache[key] = res
        return res
    # dp[i][s] = best score with systems 0..i-1 assigned covering measures up to s (exclusive end)
    dp = [dict() for _ in range(S + 1)]; back = [dict() for _ in range(S + 1)]
    dp[0][0] = 0.0
    for i in range(S):
        for s, v in list(dp[i].items()):
            # junk systems (not music of this piece): only before the first measure or after the last
            if (s == 0 or s == M) and 0 < M:
                jv = v - 1.0
                if jv > dp[i + 1].get(s, NEG):
                    dp[i + 1][s] = jv; back[i + 1][s] = (s, s, 0, 0)
            starts = [(s, 0.0, 0)]
            if i > 0 or start_range:
                for g in range(1, (max_gap if i > 0 else start_range) + 1):
                    if s + g < M: starts.append((s + g, -(gap_cost + 0.2 * g), g))
            for (s2, pen, g) in starts:
                for L, sc in scores_at(i, s2).items():
                    e = s2 + L; val = v + pen + sc
                    if val > dp[i + 1].get(e, NEG):
                        dp[i + 1][e] = val; back[i + 1][e] = (s, s2, L, g)
    if not dp[S]: return None, NEG, 0
    # end: prefer ending at M; else penalise leftover
    best_e, best_v = None, NEG
    for e, v in dp[S].items():
        adj = v - (0.0 if e == M else 0.15 * (M - e))
        if adj > best_v: best_v, best_e = adj, e
    out = []; e = best_e
    for i in range(S, 0, -1):
        s, s2, L, g = back[i][e]
        out.append(dict(start=s2, L=L, gap=g)); e = s
    out.reverse()
    return out, best_v, best_e


def bar_counters(notes):
    """model notes [[bar, pitch],...] -> Counters per bar from the first to the last bar that holds notes (empty bars kept)"""
    if not notes: return []
    lo = min(b for b, p in notes); hi = max(b for b, p in notes)
    out = [collections.Counter() for _ in range(hi - lo + 1)]
    for b, p in notes: out[b - lo][p] += 1
    return out
