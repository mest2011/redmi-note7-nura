#!/usr/bin/env python3
"""Mede as 24 cores da carta num RAW10 e calcula balanço de branco e CCM.
Uso: ccm.py arq.raw L A stride ORDEM preto TLx TLy TRx TRy BLx BLy BRx BRy saida.png
(coordenadas na imagem de meia resolução: um pixel por quadrado Bayer)"""
import sys
import numpy as np
from PIL import Image, ImageDraw

a = sys.argv
f, w, h, st, order, bl = a[1], int(a[2]), int(a[3]), int(a[4]), a[5], float(a[6])
TL, TR, BL, BR = [np.array([float(a[7 + 2 * i]), float(a[8 + 2 * i])]) for i in range(4)]
out = a[15]
d = np.fromfile(f, dtype=np.uint8)[-st * h:].reshape(h, st)[:, : w * 10 // 8].astype(np.uint16)
b = d.reshape(h, w // 4, 5)
px = np.empty((h, w // 4, 4), dtype=np.uint16)
for i in range(4):
    px[:, :, i] = (b[:, :, i] << 2) | ((b[:, :, 4] >> (2 * i)) & 3)
raw = px.reshape(h, w).astype(np.float64)
print("percentis 0.01/0.1/1:", np.percentile(raw, [0.01, 0.1, 1]))
p = {"00": raw[0::2, 0::2], "01": raw[0::2, 1::2], "10": raw[1::2, 0::2], "11": raw[1::2, 1::2]}
m = {"BGGR": ("11", "01", "10", "00"), "RGGB": ("00", "01", "10", "11"),
     "GRBG": ("01", "00", "11", "10"), "GBRG": ("10", "00", "11", "01")}[order]
img = np.stack([p[m[0]], (p[m[1]] + p[m[2]]) / 2, p[m[3]]], -1) - bl

hexes = "735244 c29682 627a9d 576c43 8580b1 67bdaa d67e2c 505ba6 c15a63 5e3c6c 9dbc40 e0a32e 383d96 469449 af363c e7c71f bb5695 0885a1 f3f3f2 c8c8c8 a0a0a0 7a7a79 555555 343434".split()
tgt = np.array([[int(x[i:i + 2], 16) / 255 for i in (0, 2, 4)] for x in hexes])
tgt = np.where(tgt <= 0.04045, tgt / 12.92, ((tgt + 0.055) / 1.055) ** 2.4)

cam = []
vis = Image.fromarray(np.clip(img / img.max() * 255 * 2, 0, 255).astype(np.uint8))
dr = ImageDraw.Draw(vis)
cell = np.linalg.norm(TR - TL) / 5
r = max(2, int(cell * 0.18))
for k in range(24):
    i, j = divmod(k, 6)
    u, v = j / 5, i / 3
    c = (1 - u) * (1 - v) * TL + u * (1 - v) * TR + (1 - u) * v * BL + u * v * BR
    x, y = int(round(c[0])), int(round(c[1]))
    cam.append(np.median(img[y - r:y + r + 1, x - r:x + r + 1].reshape(-1, 3), 0))
    dr.rectangle([x - r, y - r, x + r, y + r], outline=(255, 0, 0))
vis.save(out)
cam = np.array(cam)
print("branco bruto RGB:", cam[18].round(1), " máx bruto:", raw.max())
# balanço de branco pelos cinzas 19-22
neu = cam[18:22]
gains = neu[:, 1].sum() / neu.sum(0)
print("ganhos AWB (R,G,B):", gains.round(3))
cw = cam * gains
# escala: luminância dos cinzas da câmera = dos alvos
s = (tgt[18:22] @ [0.2126, 0.7152, 0.0722]).sum() / cw[18:22, 1].sum()
cw = cw * s
use = list(range(0, 23))
X, Y = cw[use], tgt[use]
M = np.zeros((3, 3))
# mínimos quadrados com soma de cada linha = 1 (branco continua branco)
for c in range(3):
    A = np.hstack([X.T @ X, np.ones((3, 1))])
    A = np.vstack([A, [1, 1, 1, 0]])
    rhs = np.concatenate([X.T @ Y[:, c], [1]])
    M[c] = np.linalg.solve(A, rhs)[:3]
print("CCM:")
for row in M:
    print("  [%8.4f, %8.4f, %8.4f]" % tuple(row))


def de(a_, b_):
    def lab(c_):
        xyz = c_ @ np.array([[0.4124, 0.2126, 0.0193], [0.3576, 0.7152, 0.1192], [0.1805, 0.0722, 0.9505]])
        xyz = xyz / [0.9505, 1, 1.089]
        f_ = np.where(xyz > 0.008856, np.cbrt(np.clip(xyz, 0, None)), 7.787 * xyz + 16 / 116)
        return np.stack([116 * f_[:, 1] - 16, 500 * (f_[:, 0] - f_[:, 1]), 200 * (f_[:, 1] - f_[:, 2])], 1)
    return np.linalg.norm(lab(a_) - lab(b_), axis=1)


print("erro médio ΔE só AWB: %.1f   com CCM: %.1f" % (de(X, Y).mean(), de(np.clip(X @ M.T, 0, None), Y).mean()))
