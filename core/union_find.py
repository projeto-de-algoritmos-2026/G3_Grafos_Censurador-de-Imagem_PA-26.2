"""Conjuntos disjuntos (Union-Find) sobre indices inteiros.

Implementa as duas otimizacoes:
- compressao de caminho: cada find achata o caminho ate a raiz
- uniao por rank: a arvore mais rasa e pendurada na mais profunda

Com as duas, find e union custam O(alfa(n)) amortizado, onde alfa e a inversa
da funcao de Ackermann - menor que 5 para qualquer n imaginavel.

Os vetores sao numpy porque aqui n e o numero de pixels: centenas de milhares.
"""

from __future__ import annotations

import numpy as np

SEM_FUSAO = -1


class UnionFind:
    def __init__(self, total: int) -> None:
        self._pai = np.arange(total, dtype=np.int32)
        self._rank = np.zeros(total, dtype=np.int8)
        self.tamanho = np.ones(total, dtype=np.int32)
        self.grupos = total

    def find(self, x: int) -> int:
        """Raiz do grupo de x, achatando o caminho percorrido."""
        pai = self._pai
        raiz = x
        while pai[raiz] != raiz:
            raiz = pai[raiz]
        while pai[x] != raiz:
            pai[x], x = raiz, pai[x]
        return int(raiz)

    def union(self, a: int, b: int) -> int:
        """Une os grupos de a e b.

        Retorna a raiz resultante, ou SEM_FUSAO se ja estavam no mesmo grupo.
        Devolver a raiz permite a quem chama manter dados por componente sem
        precisar de um segundo find.
        """
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return SEM_FUSAO
        if self._rank[ra] < self._rank[rb]:
            ra, rb = rb, ra
        self._pai[rb] = ra
        if self._rank[ra] == self._rank[rb]:
            self._rank[ra] += 1
        self.tamanho[ra] += self.tamanho[rb]
        self.grupos -= 1
        return int(ra)

    def conectados(self, a: int, b: int) -> bool:
        return self.find(a) == self.find(b)

    def rotulos(self, total: int) -> np.ndarray:
        """Vetor com a raiz de cada elemento, util para gerar mapas de regiao."""
        return np.fromiter((self.find(i) for i in range(total)),
                           dtype=np.int32, count=total)
