"""A imagem como grafo em grade.

Modelagem:
    vertice = pixel
    aresta  = par de pixels adjacentes (vizinhanca 4)
    peso    = distancia euclidiana entre as cores dos dois pixels

Uma imagem H x L tem H*L vertices e 2*H*L - H - L arestas. Para 512x512 isso
da 262.144 vertices e 523.264 arestas, o que exige montar os pesos de forma
vetorizada: os lacos ficam apenas onde a ordem de processamento importa.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image

LADO_MAXIMO_PADRAO = 512


@dataclass
class GrafoImagem:
    """Grafo em grade derivado de uma imagem RGB.

    As arestas ficam em tres vetores paralelos (origens, destinos, pesos) em
    vez de lista de adjacencia: e a forma que o Kruskal consome diretamente, e
    a vizinhanca de um pixel pode ser calculada por aritmetica quando
    necessario, sem custo de armazenamento.
    """

    imagem: np.ndarray                         # (altura, largura, 3) uint8
    origens: np.ndarray = field(repr=False)
    destinos: np.ndarray = field(repr=False)
    pesos: np.ndarray = field(repr=False)

    @property
    def altura(self) -> int:
        return int(self.imagem.shape[0])

    @property
    def largura(self) -> int:
        return int(self.imagem.shape[1])

    @property
    def total_vertices(self) -> int:
        return self.altura * self.largura

    @property
    def total_arestas(self) -> int:
        return int(len(self.pesos))

    def indice(self, linha: int, coluna: int) -> int:
        """Converte coordenada de pixel em indice de vertice."""
        return linha * self.largura + coluna

    def posicao(self, indice: int) -> tuple[int, int]:
        """Converte indice de vertice em coordenada de pixel."""
        return divmod(int(indice), self.largura)

    def dentro(self, linha: int, coluna: int) -> bool:
        return 0 <= linha < self.altura and 0 <= coluna < self.largura

    def vizinhos(self, linha: int, coluna: int):
        """Vizinhos de 4 de um pixel, ja recortados pela borda da imagem."""
        for dl, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nl, nc = linha + dl, coluna + dc
            if self.dentro(nl, nc):
                yield nl, nc


def construir(imagem: np.ndarray) -> GrafoImagem:
    """Monta as arestas horizontais e verticais com seus pesos.

    Pixels de cor parecida ficam ligados por arestas baratas; a fronteira
    entre dois objetos aparece como uma faixa de arestas caras. E essa
    diferenca que a segmentacao explora.
    """
    if imagem.ndim != 3 or imagem.shape[2] < 3:
        raise ValueError("A imagem precisa ser RGB (altura, largura, 3)")
    cores = np.ascontiguousarray(imagem[:, :, :3], dtype=np.float32)
    altura, largura = cores.shape[:2]
    if altura < 2 or largura < 2:
        raise ValueError("A imagem precisa ter ao menos 2x2 pixels")

    indices = np.arange(altura * largura, dtype=np.int32).reshape(altura, largura)

    # (l, c) - (l, c+1)
    dif_h = np.linalg.norm(cores[:, 1:] - cores[:, :-1], axis=2)
    # (l, c) - (l+1, c)
    dif_v = np.linalg.norm(cores[1:] - cores[:-1], axis=2)

    return GrafoImagem(
        imagem=cores.astype(np.uint8),
        origens=np.concatenate([indices[:, :-1].ravel(), indices[:-1].ravel()]),
        destinos=np.concatenate([indices[:, 1:].ravel(), indices[1:].ravel()]),
        pesos=np.concatenate([dif_h.ravel(), dif_v.ravel()]).astype(np.float32),
    )


def carregar(caminho: str | Path, lado_maximo: int | None = LADO_MAXIMO_PADRAO) -> np.ndarray:
    """Le a imagem do disco em RGB, reduzindo se for grande demais.

    A reducao existe porque o custo dos algoritmos cresce com o numero de
    pixels: dobrar o lado quadruplica os vertices. Manter o lado maximo em 512
    deixa a interface responsiva sem alterar o comportamento dos algoritmos.
    """
    figura = Image.open(caminho).convert("RGB")
    if lado_maximo and max(figura.size) > lado_maximo:
        escala = lado_maximo / max(figura.size)
        novo = (max(2, round(figura.width * escala)), max(2, round(figura.height * escala)))
        figura = figura.resize(novo, Image.LANCZOS)
    return np.asarray(figura, dtype=np.uint8)
