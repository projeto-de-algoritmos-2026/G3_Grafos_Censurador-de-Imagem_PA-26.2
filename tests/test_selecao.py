"""Testes do EXTRA - flood fill."""

import unittest

import numpy as np

from apoio import duas_metades, quatro_quadrantes
from core import grafo_imagem, selecao


class TestFloodFill(unittest.TestCase):
    def test_seleciona_apenas_a_metade_clicada(self):
        grafo = grafo_imagem.construir(duas_metades(20, 20))
        resultado = selecao.preencher(grafo, 10, 2, tolerancia=10)
        self.assertEqual(resultado.pixels, 20 * 10)
        self.assertTrue(resultado.mascara[:, :10].all())
        self.assertFalse(resultado.mascara[:, 10:].any())

    def test_tolerancia_alta_toma_a_imagem_toda(self):
        grafo = grafo_imagem.construir(quatro_quadrantes(20))
        resultado = selecao.preencher(grafo, 0, 0, tolerancia=1000)
        self.assertEqual(resultado.pixels, 400)

    def test_regiao_desconexa_nao_e_incluida(self):
        """Duas areas da mesma cor, separadas: so a conectada entra."""
        imagem = np.zeros((10, 10, 3), dtype=np.uint8)
        imagem[:, :3] = (255, 0, 0)
        imagem[:, 7:] = (255, 0, 0)   # mesma cor, mas do outro lado
        grafo = grafo_imagem.construir(imagem)
        resultado = selecao.preencher(grafo, 5, 1, tolerancia=10)
        self.assertEqual(resultado.pixels, 30)
        self.assertFalse(resultado.mascara[:, 7:].any())

    def test_semente_fora_da_imagem(self):
        grafo = grafo_imagem.construir(quatro_quadrantes(8))
        with self.assertRaises(ValueError):
            selecao.preencher(grafo, 99, 0)

    def test_tolerancia_negativa(self):
        grafo = grafo_imagem.construir(quatro_quadrantes(8))
        with self.assertRaises(ValueError):
            selecao.preencher(grafo, 0, 0, tolerancia=-1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
