#!/usr/bin/env python3
"""Converte RAW10 empacotado (CSI-2) em PNG. Uso: raw2png.py arq.raw L A ORDEM saida.png [quadro] [stride]"""
import sys
import numpy as np
from PIL import Image

f, w, h, order, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4], sys.argv[5]
frame = int(sys.argv[6]) if len(sys.argv) > 6 else -1
stride = int(sys.argv[7]) if len(sys.argv) > 7 else (w * 10 // 8)
fs = stride * h
d = np.fromfile(f, dtype=np.uint8)
n = len(d) // fs
d = d[(frame % n) * fs:(frame % n + 1) * fs].reshape(h, stride)[:, : w * 10 // 8].astype(np.uint16)
b = d.reshape(h, w // 4, 5)
px = np.empty((h, w // 4, 4), dtype=np.uint16)
for i in range(4):
    px[:, :, i] = (b[:, :, i] << 2) | ((b[:, :, 4] >> (2 * i)) & 3)
raw = px.reshape(h, w).astype(np.float32)
print("quadros", n, "min", raw.min(), "max", raw.max(), "media", round(float(raw.mean()), 1))
# planos por posição
p = {"00": raw[0::2, 0::2], "01": raw[0::2, 1::2], "10": raw[1::2, 0::2], "11": raw[1::2, 1::2]}
m = {"BGGR": ("11", "01", "10", "00"), "RGGB": ("00", "01", "10", "11"),
     "GRBG": ("01", "00", "11", "10"), "GBRG": ("10", "00", "11", "01")}[order]
R, G, B = p[m[0]], (p[m[1]] + p[m[2]]) / 2, p[m[3]]
bl = 64.0
rgb = np.stack([R, G, B], axis=-1) - bl
rgb = np.clip(rgb, 0, None)
# balanço de branco cinza e normalização pelo percentil 99
means = rgb.reshape(-1, 3).mean(axis=0) + 1e-6
rgb = rgb * (means[1] / means)
rgb = rgb / max(np.percentile(rgb, 99.5), 1.0)
rgb = np.clip(rgb, 0, 1) ** (1 / 2.2)
Image.fromarray((rgb * 255).astype(np.uint8)).save(out)
print("salvo", out, rgb.shape)
