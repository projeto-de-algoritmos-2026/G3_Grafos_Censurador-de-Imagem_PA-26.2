"""Testes da estrutura do grafo de pixels."""

import unittest

import numpy as np

from apoio import duas_metades, quatro_quadrantes
from core import grafo_imagem


class TestConstrucao(unittest.TestCase):
    def test_contagem_de_vertices_e_arestas(self):
        """H*L vertices e 2*H*L - H - L arestas na vizinhanca 4."""
        for altura, largura in [(2, 2), (10, 7), (20, 20)]:
            grafo = grafo_imagem.construir(np.zeros((altura, largura, 3), dtype=np.uint8))
            with self.subTest(forma=(altura, largura)):
                self.assertEqual(grafo.total_vertices, altura * largura)
                self.assertEqual(grafo.total_arestas,
                                 2 * altura * largura - altura - largura)

    def test_peso_e_diferenca_de_cor(self):
        grafo = grafo_imagem.construir(duas_metades(4, 4))
        # dentro de cada metade a diferenca e zero; na fronteira e a distancia
        # entre preto e branco: sqrt(3) * 255
        self.assertAlmostEqual(float(grafo.pesos.max()), np.sqrt(3) * 255, places=2)
        self.assertEqual(float(grafo.pesos.min()), 0.0)

    def test_indice_e_posicao_sao_inversos(self):
        grafo = grafo_imagem.construir(quatro_quadrantes(8))
        for linha, coluna in [(0, 0), (3, 5), (7, 7)]:
            self.assertEqual(grafo.posicao(grafo.indice(linha, coluna)), (linha, coluna))

    def test_vizinhanca_respeita_a_borda(self):
        grafo = grafo_imagem.construir(quatro_quadrantes(8))
        self.assertEqual(len(list(grafo.vizinhos(0, 0))), 2)      # canto
        self.assertEqual(len(list(grafo.vizinhos(0, 3))), 3)      # lateral
        self.assertEqual(len(list(grafo.vizinhos(3, 3))), 4)      # interior

    def test_imagem_invalida(self):
        with self.assertRaises(ValueError):
            grafo_imagem.construir(np.zeros((5, 5), dtype=np.uint8))       # sem canais
        with self.assertRaises(ValueError):
            grafo_imagem.construir(np.zeros((1, 9, 3), dtype=np.uint8))    # fina demais


class TestUnionFind(unittest.TestCase):
    def test_uniao_busca_e_tamanho(self):
        from core.union_find import UnionFind, SEM_FUSAO

        uf = UnionFind(6)
        self.assertNotEqual(uf.union(0, 1), SEM_FUSAO)
        self.assertEqual(uf.union(0, 1), SEM_FUSAO)  # ja estavam juntos
        uf.union(1, 2)
        self.assertTrue(uf.conectados(0, 2))
        self.assertFalse(uf.conectados(0, 3))
        self.assertEqual(int(uf.tamanho[uf.find(0)]), 3)
        self.assertEqual(uf.grupos, 4)

    def test_rotulos_agrupam_corretamente(self):
        from core.union_find import UnionFind

        uf = UnionFind(4)
        uf.union(0, 1)
        uf.union(2, 3)
        rotulos = uf.rotulos(4)
        self.assertEqual(rotulos[0], rotulos[1])
        self.assertEqual(rotulos[2], rotulos[3])
        self.assertNotEqual(rotulos[0], rotulos[2])


if __name__ == "__main__":
    unittest.main(verbosity=2)
