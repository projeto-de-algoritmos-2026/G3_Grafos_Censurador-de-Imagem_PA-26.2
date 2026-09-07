"""EXTRA - Selecao por regiao conectada (flood fill).

Nao conta como um dos metodos do trabalho: e uma busca em largura simples,
sem custo acumulado nem decisao de otimalidade. Esta aqui porque usa o mesmo
grafo em grade e serve de contraste didatico com os outros dois:

    flood fill : percorre enquanto a COR do pixel estiver perto da semente
    Dijkstra   : percorre minimizando o CUSTO ACUMULADO ate cada pixel
    Kruskal    : nao percorre - ordena arestas e funde regioes

E a varinha magica dos editores de imagem.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

import numpy as np

from .grafo_imagem import GrafoImagem


@dataclass
class ResultadoSelecao:
    mascara: np.ndarray
    pixels: int
    visitados: int

    @property
    def resumo(self) -> str:
        return f"{self.pixels} pixels selecionados | {self.visitados} visitados"


def preencher(grafo: GrafoImagem, linha: int, coluna: int,
              tolerancia: float = 40.0) -> ResultadoSelecao:
    """Busca em largura a partir do pixel semente, limitada por tolerancia.

    A comparacao e sempre contra a cor da semente, nao contra a do vizinho
    imediato: comparar com o vizinho permitiria a selecao escorregar por um
    degrade e tomar a imagem inteira.
    """
    if not grafo.dentro(linha, coluna):
        raise ValueError("A semente precisa estar dentro da imagem")
    if tolerancia < 0:
        raise ValueError("A tolerancia nao pode ser negativa")

    cores = grafo.imagem.astype(np.float32)
    dentro_da_faixa = np.linalg.norm(cores - cores[linha, coluna], axis=2) <= tolerancia

    mascara = np.zeros((grafo.altura, grafo.largura), dtype=bool)
    if not dentro_da_faixa[linha, coluna]:
        return ResultadoSelecao(mascara, 0, 0)

    fila = deque([(linha, coluna)])
    mascara[linha, coluna] = True
    visitados = 0
    while fila:
        atual = fila.popleft()
        visitados += 1
        for nl, nc in grafo.vizinhos(*atual):
            if dentro_da_faixa[nl, nc] and not mascara[nl, nc]:
                mascara[nl, nc] = True
                fila.append((nl, nc))

    return ResultadoSelecao(mascara, int(mascara.sum()), visitados)
