"""Mede o custo dos dois metodos conforme o numero de pixels cresce.

Gera a tabela que sustenta a analise de complexidade no relatorio: dobrar o
lado da imagem quadruplica os vertices, e a curva de tempo mostra se o
comportamento observado bate com O(E log E) do Kruskal e O(E log V) do
Dijkstra.
"""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np
from PIL import Image

from core import grafo_imagem, segmentacao, tesoura

LADOS = (64, 128, 192, 256, 384, 512)


def executar(caminho: str | Path) -> None:
    original = Image.open(caminho).convert("RGB")
    print(f"{'lado':>6} {'vertices':>10} {'arestas':>10} "
          f"{'grafo(s)':>9} {'kruskal(s)':>11} {'dijkstra(s)':>12} {'regioes':>8}")
    print("-" * 72)

    for lado in LADOS:
        imagem = np.asarray(original.resize((lado, lado), Image.LANCZOS), dtype=np.uint8)

        inicio = time.perf_counter()
        grafo = grafo_imagem.construir(imagem)
        tempo_grafo = time.perf_counter() - inicio

        inicio = time.perf_counter()
        resultado = segmentacao.segmentar(grafo, k=600, tamanho_minimo=80)
        tempo_kruskal = time.perf_counter() - inicio

        custo = tesoura.mapa_de_custo(grafo)
        inicio = time.perf_counter()
        tesoura.tracar(grafo, (2, 2), (lado - 3, lado - 3), custo)
        tempo_dijkstra = time.perf_counter() - inicio

        print(f"{lado:>6} {grafo.total_vertices:>10,} {grafo.total_arestas:>10,} "
              f"{tempo_grafo:>9.3f} {tempo_kruskal:>11.3f} {tempo_dijkstra:>12.3f} "
              f"{resultado.total_regioes:>8}".replace(",", "."))
