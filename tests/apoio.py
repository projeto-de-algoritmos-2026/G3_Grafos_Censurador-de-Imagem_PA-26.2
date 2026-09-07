"""Imagens sinteticas para os testes.

Usar imagem construida a mao em vez de foto permite saber a resposta certa de
antemao, o que e o que torna o teste util.
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def duas_metades(altura=20, largura=20) -> np.ndarray:
    """Metade esquerda preta, metade direita branca. Uma unica borda vertical."""
    img = np.zeros((altura, largura, 3), dtype=np.uint8)
    img[:, largura // 2:] = 255
    return img


def quatro_quadrantes(lado=20) -> np.ndarray:
    """Quatro blocos de cores bem distintas."""
    img = np.zeros((lado, lado, 3), dtype=np.uint8)
    meio = lado // 2
    img[:meio, :meio] = (255, 0, 0)
    img[:meio, meio:] = (0, 255, 0)
    img[meio:, :meio] = (0, 0, 255)
    img[meio:, meio:] = (255, 255, 0)
    return img


def ruido(altura=30, largura=30, semente=7) -> np.ndarray:
    gerador = np.random.default_rng(semente)
    return gerador.integers(0, 256, size=(altura, largura, 3), dtype=np.uint8)
