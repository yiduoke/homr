"""finetune2.py (D30): finetune.py with named sampling weights for the sources of build_mixture2.py (real_piano, real_song, rendered, varied, real_curved,
real_schott, varied_s; a source that is absent from the mixture is ignored) and a per-source report of the validation pairs (accuracy, grand recall).
Same network, losses, augmentations, optimiser and budget as finetune.py. Original docstring follows.

Fine-tunes the shipped staff relation model (vertical pairs) on the mixture of real scans and rendered pages.

The shipped ONNX has the batch norms folded into the convolutions, so the network is rebuilt without batch norm and the folded
weights are loaded; the architecture and the export are the same as training/staff_relations/train.py (Conv/Relu/MaxPool/Gemm).
Augmentations are those of train.py (erase clefs, edge lines, cut image border, contrast).

usage: python finetune.py MIXTURE.npz OUT.onnx [--epochs 12 --lr 1e-4 --seed 0 --weights w_real,w_song,w_rendered]
MIXTURE.npz: crops uint8 (n,5,96,96), labels, source (real_piano|real_song|rendered), split (train|val), group (volume/piece), 
"""
import argparse, sys, json
import numpy as np
import onnx
from onnx import numpy_helper
import torch
from torch import nn

sys.path.insert(0, "/Users/yiduoke/Documents/homr/run/rel_wt")
from homr.staff_relations import channels, crop_height, crop_width, model_path  # noqa: E402
from training.staff_relations import train as T  # noqa: E402


class Net(nn.Module):
    def __init__(self):
        super().__init__()
        def block(i, o):
            return nn.Sequential(nn.Conv2d(i, o, 3, padding=1), nn.ReLU(), nn.Conv2d(o, o, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2))
        self.convolutions = nn.Sequential(block(channels, 24), block(24, 48), block(48, 64), block(64, 96), nn.Conv2d(96, 32, 1))
        flat = 32 * (crop_height // 16) * (crop_width // 16)
        self.head = nn.Sequential(nn.Linear(flat, 128), nn.ReLU(), nn.Dropout(0.3), nn.Linear(128, 3))

    def forward(self, crop, feats=None):
        return self.head(self.convolutions(crop).flatten(1))


def load_shipped(path):
    m = onnx.load(path)
    init = {i.name: numpy_helper.to_array(i) for i in m.graph.initializer}
    convs = [n for n in m.graph.node if n.op_type == "Conv"]
    net = Net()
    torch_convs = [mod for mod in net.convolutions.modules() if isinstance(mod, nn.Conv2d)]
    assert len(convs) == len(torch_convs)
    for node, mod in zip(convs, torch_convs):
        w = [init[n] for n in node.input if n in init]
        mod.weight.data = torch.from_numpy(w[0].copy()); mod.bias.data = torch.from_numpy(w[1].copy())
    net.head[0].weight.data = torch.from_numpy(init["head.0.weight"].copy()); net.head[0].bias.data = torch.from_numpy(init["head.0.bias"].copy())
    net.head[3].weight.data = torch.from_numpy(init["head.3.weight"].copy()); net.head[3].bias.data = torch.from_numpy(init["head.3.bias"].copy())
    return net


def evaluate(net, crops, labels, bs=256, device="cpu"):
    net.eval(); out = []
    with torch.no_grad():
        for s in range(0, len(labels), bs):
            x = torch.from_numpy(crops[s:s + bs]).float().to(device) / 255
            out.append(torch.softmax(net(x), 1).cpu().numpy())
    return np.concatenate(out) if out else np.zeros((0, 3))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mixture"); ap.add_argument("output")
    ap.add_argument("--epochs", type=int, default=12); ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--weights", default="real_piano=3,real_song=2,rendered=2,varied=3,real_curved=2,real_schott=3,varied_s=3",
                    help="sampling weight per source (split evenly over the three classes)")
    ap.add_argument("--steps-per-epoch", type=int, default=150)
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--device", default="cpu")
    a = ap.parse_args()
    torch.set_num_threads(a.threads); torch.manual_seed(a.seed); np.random.seed(a.seed)
    d = np.load(a.mixture, allow_pickle=True)
    crops, labels, source, split, group = d["crops"], d["labels"], d["source"], d["split"], d["group"]
    tr, va = split == "train", split == "val"
    w_by = {k: float(v) for k, v in (x.split("=") for x in a.weights.split(","))}
    # sampling weight per pair: source weight / pairs of that (source, class)
    weight = np.zeros(len(labels))
    for s, w in w_by.items():
        for c in range(3):
            m = tr & (source == s) & (labels == c)
            if m.sum():
                weight[m] = w / m.sum()
    weight /= weight.sum()
    print("train", tr.sum(), "val", va.sum(), {s: int((tr & (source == s)).sum()) for s in w_by}, flush=True)
    net = load_shipped(model_path)
    # sanity: the rebuilt net reproduces the shipped onnx
    import onnxruntime as ort
    sess = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
    x = torch.from_numpy(crops[va][:64]).float() / 255
    ref = sess.run(None, {"crop": x.numpy()})[0]
    net.eval(); mine = net(x).detach().numpy()
    print("max |logit diff| to shipped onnx:", float(np.abs(ref - mine).max()))
    net.to(a.device)
    opt = torch.optim.AdamW(net.parameters(), lr=a.lr, weight_decay=1e-4)
    steps = a.epochs * a.steps_per_epoch
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, a.lr, total_steps=steps, pct_start=0.15)
    lossf = nn.CrossEntropyLoss()
    train_idx = np.nonzero(tr)[0]
    for ep in range(a.epochs):
        net.train(); tot = 0
        for _ in range(a.steps_per_epoch):
            idx = np.sort(np.random.choice(len(labels), 64, p=weight))
            x = torch.from_numpy(crops[idx]).float().to(a.device) / 255; y = torch.from_numpy(labels[idx]).to(a.device)
            x = T._add_edge_lines(T._erase_clefs(x, 0.3), 0.3)
            x = T._cut_image_border(x, 0.2)
            loss = lossf(net(T._augment(x)), y)
            opt.zero_grad(); loss.backward(); opt.step(); sched.step(); tot += loss.item()
        p = evaluate(net, crops[va], labels[va], device=a.device)
        acc = {}
        for s in w_by:
            m = source[va] == s
            if m.sum():
                g = m & (labels[va] == 2)
                acc[s] = (round(float((p[m].argmax(1) == labels[va][m]).mean()), 4), round(float((p[g].argmax(1) == 2).mean()), 3) if g.sum() else None)
        print(f"epoch {ep}: loss {tot / a.steps_per_epoch:.4f} val acc {acc}", flush=True)
    net.eval().cpu()
    torch.save(net.state_dict(), a.output.replace(".onnx", ".pth"))
    torch.onnx.export(net, (torch.zeros(1, channels, crop_height, crop_width),), a.output, input_names=["crop"],
                      output_names=["logits"], dynamic_axes={"crop": {0: "batch"}, "logits": {0: "batch"}}, opset_version=17, dynamo=False)
    print("wrote", a.output)


if __name__ == "__main__":
    main()
