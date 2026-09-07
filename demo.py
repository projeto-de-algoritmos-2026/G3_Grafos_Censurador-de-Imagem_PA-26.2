"""Gera um painel comparativo dos tres algoritmos sobre a mesma imagem."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from core import grafo_imagem, segmentacao, tesoura, selecao
from gui import pintura

LEGENDA = 26
SAIDA = "resultado.png"


def _rotular(arr: np.ndarray, texto: str) -> Image.Image:
    base = Image.fromarray(arr.astype(np.uint8))
    tela = Image.new("RGB", (base.width, base.height + LEGENDA), (238, 241, 244))
    tela.paste(base, (0, 0))
    ImageDraw.Draw(tela).text((6, base.height + 7), texto, fill=(22, 35, 47))
    return tela


def executar(caminho: str | Path) -> None:
    imagem = grafo_imagem.carregar(caminho)
    grafo = grafo_imagem.construir(imagem)
    print(f"Grafo: {grafo.total_vertices:,} vertices, {grafo.total_arestas:,} arestas")

    seg = segmentacao.segmentar(grafo, k=600, tamanho_minimo=80)
    print("Kruskal:", seg.resumo)

    altura, largura = grafo.altura, grafo.largura
    sel = selecao.preencher(grafo, altura // 8, largura - largura // 8, tolerancia=42)
    print("Flood fill:", sel.resumo)

    rota = tesoura.tracar_poligonal(
        grafo,
        [(altura // 5, largura // 4), (altura // 2, largura // 6),
         (altura - altura // 6, largura // 2)])
    print("Dijkstra:", rota.resumo)

    quadros = [
        _rotular(imagem, "original"),
        _rotular(pintura.pintar_contornos(imagem, segmentacao.contornos(seg.rotulos)),
                 f"Kruskal: {seg.total_regioes} regioes"),
        _rotular(segmentacao.cor_media(imagem, seg.rotulos), "regioes pela cor media"),
        _rotular(pintura.marcar(imagem, sel.mascara, pintura.TURQUESA),
                 f"flood fill: {sel.pixels} px"),
        _rotular(pintura.pintar_caminho(imagem, rota.caminho),
                 f"Dijkstra: custo {rota.custo:.0f}"),
    ]

    largura_total = sum(q.width for q in quadros) + 8 * (len(quadros) - 1)
    painel = Image.new("RGB", (largura_total, quadros[0].height), (238, 241, 244))
    x = 0
    for quadro in quadros:
        painel.paste(quadro, (x, 0))
        x += quadro.width + 8
    painel.save(SAIDA)
    print(f"\nPainel salvo em {SAIDA}")
