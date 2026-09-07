"""Composicao das camadas visuais sobre a imagem.

BASE COMPARTILHADA. Cada metodo produz um resultado diferente (rotulos,
mascara, caminho) e todos precisam virar pixels na tela. Centralizar aqui
evita que os dois lados escrevam a mesma logica de sobreposicao.
"""

from __future__ import annotations

import numpy as np

LARANJA = np.array([255, 90, 0], dtype=np.float32)
TURQUESA = np.array([0, 200, 190], dtype=np.float32)


def marcar(imagem: np.ndarray, mascara: np.ndarray, cor: np.ndarray,
           opacidade: float = 0.6) -> np.ndarray:
    """Mistura uma cor sobre os pixels indicados pela mascara."""
    saida = imagem.astype(np.float32).copy()
    saida[mascara] = saida[mascara] * (1 - opacidade) + cor * opacidade
    return saida.astype(np.uint8)


def pintar_contornos(imagem: np.ndarray, borda: np.ndarray) -> np.ndarray:
    """Desenha as fronteiras entre regioes por cima da imagem original."""
    saida = imagem.copy()
    saida[borda] = LARANJA.astype(np.uint8)
    return saida


def pintar_caminho(imagem: np.ndarray, caminho: list[tuple[int, int]],
                   espessura: int = 1) -> np.ndarray:
    """Desenha o traco do caminho, engrossado para ficar visivel."""
    saida = imagem.copy()
    altura, largura = saida.shape[:2]
    for linha, coluna in caminho:
        l0, l1 = max(0, linha - espessura), min(altura, linha + espessura + 1)
        c0, c1 = max(0, coluna - espessura), min(largura, coluna + espessura + 1)
        saida[l0:l1, c0:c1] = LARANJA.astype(np.uint8)
    return saida


def marcar_ponto(imagem: np.ndarray, ponto: tuple[int, int], raio: int = 4,
                 cor: np.ndarray = TURQUESA) -> np.ndarray:
    """Marca um clique do usuario com um quadrado cheio."""
    saida = imagem.copy()
    altura, largura = saida.shape[:2]
    linha, coluna = ponto
    saida[max(0, linha - raio):min(altura, linha + raio + 1),
          max(0, coluna - raio):min(largura, coluna + raio + 1)] = cor.astype(np.uint8)
    return saida
