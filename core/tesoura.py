"""METODO 2 - Tesoura inteligente (livewire) por Dijkstra.

O QUE FAZ
    O usuario clica em dois pontos e o algoritmo traca sozinho o contorno do
    objeto entre eles. E o laco magnetico dos editores de imagem.

COMO
    O mesmo grafo em grade, mas com outro custo. Aqui o peso nao esta na
    aresta e sim no pixel de chegada: atravessar um pixel de borda e barato,
    atravessar area lisa e caro. Como o Dijkstra minimiza o custo acumulado, o
    caminho mais barato entre os dois cliques e aquele que passa o maior tempo
    possivel em cima de bordas - ou seja, contornando o objeto.

    O custo por pixel vem da magnitude do gradiente: onde a imagem muda de cor
    depressa, ha borda. Um piso pequeno e somado ao custo para que nenhum
    pixel custe zero, o que faria surgirem caminhos gratuitos arbitrariamente
    longos ao longo de uma mesma borda.
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from math import inf

import numpy as np

from .grafo_imagem import GrafoImagem

PISO_DE_CUSTO = 0.05


@dataclass
class ResultadoCaminho:
    caminho: list[tuple[int, int]] = field(default_factory=list)
    custo: float = inf
    expandidos: int = 0          # pixels retirados da fila de prioridade
    enfileirados: int = 0        # pixels que chegaram a entrar na fila
    sucesso: bool = False

    @property
    def resumo(self) -> str:
        if not self.sucesso:
            return "Nao ha caminho entre os dois pontos."
        return (f"{len(self.caminho)} pixels | custo {self.custo:.1f} | "
                f"{self.expandidos} pixels expandidos")


def gradiente(imagem: np.ndarray) -> np.ndarray:
    """Magnitude do gradiente por diferencas centrais, calculada a mao.

    Nas bordas da imagem a derivada nao existe nos dois sentidos, entao as
    linhas e colunas extremas ficam em zero - o que tambem evita que o
    caminho se agarre na moldura da imagem.
    """
    cinza = imagem.astype(np.float32).mean(axis=2)
    gx = np.zeros_like(cinza)
    gy = np.zeros_like(cinza)
    gx[:, 1:-1] = cinza[:, 2:] - cinza[:, :-2]
    gy[1:-1, :] = cinza[2:, :] - cinza[:-2, :]
    return np.hypot(gx, gy)


def mapa_de_custo(grafo: GrafoImagem, reforco: float = 1.0) -> np.ndarray:
    """Custo de pisar em cada pixel: baixo sobre borda, alto sobre area lisa."""
    if reforco <= 0:
        raise ValueError("O reforco precisa ser maior que zero")
    magnitude = gradiente(grafo.imagem)
    maximo = float(magnitude.max()) or 1.0
    return (1.0 - magnitude / maximo) * reforco + PISO_DE_CUSTO


def tracar(grafo: GrafoImagem, inicio: tuple[int, int], fim: tuple[int, int],
           custo_pixel: np.ndarray | None = None) -> ResultadoCaminho:
    """Dijkstra sobre o grafo de pixels, do clique inicial ao clique final.

    A fila de prioridade guarda (custo acumulado, pixel). Cada pixel e fechado
    na primeira retirada: como todos os custos sao positivos, nenhuma retirada
    posterior poderia melhorar um pixel ja fechado. Entradas obsoletas sao
    descartadas na saida da fila, o que dispensa a operacao de decrease-key.
    """
    if custo_pixel is None:
        custo_pixel = mapa_de_custo(grafo)
    if not (grafo.dentro(*inicio) and grafo.dentro(*fim)):
        raise ValueError("Os pontos precisam estar dentro da imagem")

    resultado = ResultadoCaminho()
    if inicio == fim:
        resultado.caminho = [inicio]
        resultado.custo = 0.0
        resultado.sucesso = True
        return resultado

    altura, largura = grafo.altura, grafo.largura
    distancia = np.full((altura, largura), inf, dtype=np.float64)
    fechado = np.zeros((altura, largura), dtype=bool)
    anterior: dict[tuple[int, int], tuple[int, int]] = {}

    distancia[inicio] = 0.0
    fila: list[tuple[float, tuple[int, int]]] = [(0.0, inicio)]
    resultado.enfileirados = 1

    while fila:
        custo_atual, atual = heapq.heappop(fila)
        linha, coluna = atual
        if fechado[linha, coluna]:
            continue  # entrada obsoleta: o pixel ja saiu da fila mais barato
        fechado[linha, coluna] = True
        resultado.expandidos += 1
        if atual == fim:
            break
        for nl, nc in grafo.vizinhos(linha, coluna):
            if fechado[nl, nc]:
                continue
            candidato = custo_atual + float(custo_pixel[nl, nc])
            if candidato < distancia[nl, nc]:
                distancia[nl, nc] = candidato
                anterior[(nl, nc)] = atual
                heapq.heappush(fila, (candidato, (nl, nc)))
                resultado.enfileirados += 1

    if not fechado[fim]:
        return resultado

    caminho = [fim]
    atual = fim
    while atual != inicio:
        atual = anterior[atual]
        caminho.append(atual)
    caminho.reverse()

    resultado.caminho = caminho
    resultado.custo = float(distancia[fim])
    resultado.sucesso = True
    return resultado


def tracar_poligonal(grafo: GrafoImagem, pontos: list[tuple[int, int]],
                     custo_pixel: np.ndarray | None = None,
                     fechar: bool = False) -> ResultadoCaminho:
    """Encadeia varios cliques: contorna o objeto trecho a trecho.

    E assim que a ferramenta funciona na pratica - o usuario vai clicando ao
    redor do objeto e cada trecho e um Dijkstra independente. Fechar o
    poligono liga o ultimo ponto de volta ao primeiro.
    """
    if len(pontos) < 2:
        raise ValueError("Sao necessarios ao menos dois pontos")
    if custo_pixel is None:
        custo_pixel = mapa_de_custo(grafo)

    trechos = list(zip(pontos, pontos[1:]))
    if fechar:
        trechos.append((pontos[-1], pontos[0]))

    total = ResultadoCaminho(custo=0.0, sucesso=True)
    for inicio, fim in trechos:
        parcial = tracar(grafo, inicio, fim, custo_pixel)
        if not parcial.sucesso:
            return ResultadoCaminho()
        # o primeiro pixel de cada trecho repete o ultimo do trecho anterior
        total.caminho.extend(parcial.caminho if not total.caminho else parcial.caminho[1:])
        total.custo += parcial.custo
        total.expandidos += parcial.expandidos
        total.enfileirados += parcial.enfileirados
    return total
