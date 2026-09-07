"""METODO 1 - Segmentacao de imagem por Kruskal.

O QUE FAZ
    Agrupa os pixels em regioes de cor coerente. E o mesmo Kruskal da arvore
    geradora minima - percorre as arestas da mais barata para a mais cara e
    usa union-find para decidir a fusao - com uma unica diferenca: em vez de
    aceitar toda aresta que nao forma ciclo, aplica um criterio de parada.

O CRITERIO (Felzenszwalb & Huttenlocher, 2004)
    Duas regioes so se fundem se a aresta que as separa for mais barata que a
    variacao de cor que cada uma ja tolera internamente:

        peso <= min( Int(A) + k/|A| , Int(B) + k/|B| )

    Int(C) e a maior aresta interna de C, isto e, a maior diferenca de cor que
    a regiao ja aceitou. O termo k/|C| e o que da escala ao resultado: regiao
    pequena se funde com facilidade, regiao ja grande exige evidencia forte
    para crescer. Sem esse termo, uma unica aresta barata poderia colar dois
    objetos grandes por um ponto de contato.

    Se todas as arestas fossem aceitas, o resultado seria a arvore geradora
    minima da imagem inteira: uma unica regiao. O criterio e o que transforma
    a AGM em segmentacao.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .grafo_imagem import GrafoImagem
from .union_find import UnionFind, SEM_FUSAO


@dataclass
class ResultadoSegmentacao:
    rotulos: np.ndarray                  # (altura, largura) int32
    total_regioes: int
    fusoes: int = 0                      # arestas aceitas
    descartes_ciclo: int = 0             # arestas internas a uma regiao
    descartes_criterio: int = 0          # reprovadas pelo criterio de fusao
    parametros: dict = field(default_factory=dict)

    @property
    def resumo(self) -> str:
        return (f"{self.total_regioes} regioes | {self.fusoes} fusoes | "
                f"{self.descartes_ciclo} arestas internas | "
                f"{self.descartes_criterio} reprovadas pelo criterio")


def segmentar(grafo: GrafoImagem, k: float = 600.0,
              tamanho_minimo: int = 80) -> ResultadoSegmentacao:
    """Executa o Kruskal com criterio de fusao sobre o grafo de pixels.

    k               controla a escala: maior k produz regioes maiores.
    tamanho_minimo  regioes abaixo disso sao absorvidas na segunda passada,
                    porque ruido de sensor gera muitas regioes de poucos
                    pixels que nao representam nada na imagem.
    """
    if k <= 0:
        raise ValueError("k precisa ser maior que zero")

    total = grafo.total_vertices
    ordem = np.argsort(grafo.pesos, kind="stable")  # ordenacao: o gargalo
    origens = grafo.origens[ordem]
    destinos = grafo.destinos[ordem]
    pesos = grafo.pesos[ordem]

    conjuntos = UnionFind(total)
    interna = np.zeros(total, dtype=np.float32)  # Int(C) por raiz de componente
    resultado = ResultadoSegmentacao(
        rotulos=np.empty(0, dtype=np.int32), total_regioes=0,
        parametros={"k": k, "tamanho_minimo": tamanho_minimo})

    for i in range(len(pesos)):
        raiz_a = conjuntos.find(int(origens[i]))
        raiz_b = conjuntos.find(int(destinos[i]))
        if raiz_a == raiz_b:
            resultado.descartes_ciclo += 1
            continue

        peso = float(pesos[i])
        limite_a = interna[raiz_a] + k / conjuntos.tamanho[raiz_a]
        limite_b = interna[raiz_b] + k / conjuntos.tamanho[raiz_b]
        if peso > min(limite_a, limite_b):
            resultado.descartes_criterio += 1
            continue

        nova_raiz = conjuntos.union(raiz_a, raiz_b)
        if nova_raiz != SEM_FUSAO:
            # a maior aresta interna da uniao e a aresta que acabou de fundi-las
            interna[nova_raiz] = max(peso, interna[raiz_a], interna[raiz_b])
            resultado.fusoes += 1

    _absorver_regioes_pequenas(conjuntos, origens, destinos, tamanho_minimo)

    rotulos = conjuntos.rotulos(total).reshape(grafo.altura, grafo.largura)
    resultado.rotulos = rotulos
    resultado.total_regioes = int(len(np.unique(rotulos)))
    return resultado


def _absorver_regioes_pequenas(conjuntos: UnionFind, origens: np.ndarray,
                               destinos: np.ndarray, tamanho_minimo: int) -> None:
    """Segunda passada: funde regioes pequenas demais para serem significativas.

    Percorre as mesmas arestas ja ordenadas e funde sempre que um dos lados
    ainda nao alcancou o tamanho minimo, independentemente do criterio de cor.
    """
    if tamanho_minimo <= 1:
        return
    for i in range(len(origens)):
        raiz_a = conjuntos.find(int(origens[i]))
        raiz_b = conjuntos.find(int(destinos[i]))
        if raiz_a == raiz_b:
            continue
        if (conjuntos.tamanho[raiz_a] < tamanho_minimo
                or conjuntos.tamanho[raiz_b] < tamanho_minimo):
            conjuntos.union(raiz_a, raiz_b)


# --------------------------------------------------------------------- #
# apoio para visualizacao
# --------------------------------------------------------------------- #
def cor_media(imagem: np.ndarray, rotulos: np.ndarray) -> np.ndarray:
    """Pinta cada regiao com a cor media dos seus pixels."""
    _, indice = np.unique(rotulos.ravel(), return_inverse=True)
    total = int(indice.max()) + 1
    soma = np.zeros((total, 3), dtype=np.float64)
    contagem = np.zeros(total, dtype=np.float64)
    np.add.at(soma, indice, imagem.reshape(-1, 3).astype(np.float64))
    np.add.at(contagem, indice, 1)
    media = soma / contagem[:, None]
    return media[indice].reshape(imagem.shape).astype(np.uint8)


def contornos(rotulos: np.ndarray) -> np.ndarray:
    """Mascara booleana dos pixels que ficam na fronteira entre duas regioes."""
    borda = np.zeros(rotulos.shape, dtype=bool)
    borda[:, :-1] |= rotulos[:, :-1] != rotulos[:, 1:]
    borda[:-1, :] |= rotulos[:-1, :] != rotulos[1:, :]
    return borda


def achatar(imagem: np.ndarray, mascara: np.ndarray, k: float = 1500.0,
            tamanho_minimo: int = 80) -> np.ndarray:
    """Achata a area selecionada em manchas de cor chapada.

    E o resultado da propria segmentacao usado como efeito: os pixels da area
    sao agrupados em regioes por Kruskal e cada regiao e pintada com a sua cor
    media. O detalhe desaparece, mas as formas grandes e a paleta permanecem -
    parece pintura, nao mosaico.

    Como censura tem uma vantagem sobre o desfoque gaussiano: o desfoque e uma
    operacao linear e pode ser parcialmente revertido; aqui a informacao dentro
    de cada regiao e substituida por um unico valor e nao ha o que reverter.

    Para nao pagar o custo de segmentar a imagem inteira quando a selecao e
    pequena, a operacao roda apenas no retangulo que envolve a mascara. k
    maior produz manchas maiores, ou seja, mais achatamento.
    """
    from .grafo_imagem import construir  # import local: evita ciclo no modulo

    if not mascara.any():
        return imagem.copy()

    linhas, colunas = np.nonzero(mascara)
    l0, l1 = int(linhas.min()), int(linhas.max()) + 1
    c0, c1 = int(colunas.min()), int(colunas.max()) + 1
    if (l1 - l0) < 2 or (c1 - c0) < 2:
        return imagem.copy()

    recorte = imagem[l0:l1, c0:c1]
    rotulos = segmentar(construir(recorte), k=k,
                        tamanho_minimo=tamanho_minimo).rotulos
    achatado = cor_media(recorte, rotulos)

    saida = imagem.copy()
    dentro = mascara[l0:l1, c0:c1]
    saida[l0:l1, c0:c1][dentro] = achatado[dentro]
    return saida
