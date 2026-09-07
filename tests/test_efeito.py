"""Testes da BASE COMPARTILHADA: mascaras e efeitos."""

import unittest

import numpy as np

from apoio import duas_metades, quatro_quadrantes, ruido
from core import efeito, grafo_imagem, tesoura


class TestInteriorDoContorno(unittest.TestCase):
    def test_quadrado_fechado_preenche_o_interior(self):
        """Um contorno 10x10 desenhado a mao deve virar area de 100 px."""
        caminho = []
        for i in range(10, 20):
            caminho += [(10, i), (19, i), (i, 10), (i, 19)]
        mascara = efeito.interior_do_contorno(caminho, 40, 40)
        self.assertEqual(int(mascara.sum()), 100)          # 10x10 com a borda
        self.assertTrue(mascara[15, 15])                   # centro dentro
        self.assertFalse(mascara[5, 5])                    # fora

    def test_contorno_aberto_nao_gera_area(self):
        """Sem fechar, a inundacao escapa e nao ha area util."""
        caminho = [(10, i) for i in range(10, 30)]         # so uma linha
        mascara = efeito.interior_do_contorno(caminho, 40, 40)
        self.assertFalse(mascara.any())

    def test_interior_de_contorno_real_do_dijkstra(self):
        grafo = grafo_imagem.construir(quatro_quadrantes(40))
        rota = tesoura.tracar_poligonal(
            grafo, [(10, 10), (10, 30), (30, 30), (30, 10)], fechar=True)
        mascara = efeito.interior_do_contorno(rota.caminho, 40, 40)
        self.assertTrue(mascara.any())
        self.assertTrue(mascara[20, 20])                   # centro do quadrado
        self.assertFalse(mascara[0, 0])                    # canto da imagem

    def test_engrossar_dilata_a_mascara(self):
        mascara = np.zeros((10, 10), dtype=bool)
        mascara[5, 5] = True
        self.assertEqual(int(efeito.engrossar(mascara, 1).sum()), 5)   # cruz
        self.assertEqual(int(efeito.engrossar(mascara, 0).sum()), 1)


class TestEfeitos(unittest.TestCase):
    def setUp(self):
        self.imagem = quatro_quadrantes(40)
        self.mascara = np.zeros((40, 40), dtype=bool)
        self.mascara[10:30, 10:30] = True

    def test_efeito_nao_altera_fora_da_mascara(self):
        """Requisito central da ferramenta: o resto da foto fica intacto."""
        for nome in ("achatar", "borrar", "pixelizar", "tarjar"):
            saida = efeito.aplicar(nome, self.imagem, self.mascara, 8)
            with self.subTest(efeito=nome):
                np.testing.assert_array_equal(saida[~self.mascara],
                                              self.imagem[~self.mascara])

    def test_efeito_altera_dentro_da_mascara(self):
        """Sobre imagem com detalhe, os quatro efeitos precisam mudar algo."""
        imagem = ruido(40, 40)
        for nome in ("achatar", "borrar", "pixelizar", "tarjar"):
            saida = efeito.aplicar(nome, imagem, self.mascara, 8)
            with self.subTest(efeito=nome):
                self.assertFalse(np.array_equal(saida[self.mascara],
                                                imagem[self.mascara]))

    def test_achatar_preserva_area_ja_chapada(self):
        """Sobre cor uniforme, a media da regiao e a propria cor: nada muda.

        Nao e defeito - e a diferenca entre achatar por segmentacao e filtrar.
        O desfoque suavizaria a fronteira entre os quadrantes; o achatamento
        respeita as regioes e so remove detalhe interno, que aqui nao existe.
        """
        saida = efeito.aplicar("achatar", self.imagem, self.mascara, 10)
        np.testing.assert_array_equal(saida, self.imagem)

    def test_tarja_pinta_de_preto(self):
        saida = efeito.tarjar(self.imagem, self.mascara)
        self.assertTrue((saida[self.mascara] < 30).all())

    def test_borrar_reduz_a_variacao_local(self):
        """Desfoque tem que suavizar: o desvio padrao na area cai."""
        imagem = duas_metades(40, 40)
        mascara = np.zeros((40, 40), dtype=bool)
        mascara[:, 15:25] = True   # faixa em cima da borda preto/branco
        saida = efeito.borrar(imagem, mascara, raio=6)
        self.assertLess(saida[mascara].std(), imagem[mascara].std())

    def test_formato_e_tipo_preservados(self):
        saida = efeito.aplicar("pixelizar", self.imagem, self.mascara, 8)
        self.assertEqual(saida.shape, self.imagem.shape)
        self.assertEqual(saida.dtype, np.uint8)

    def test_mascara_vazia_devolve_a_imagem_original(self):
        vazia = np.zeros((40, 40), dtype=bool)
        np.testing.assert_array_equal(
            efeito.aplicar("borrar", self.imagem, vazia, 8), self.imagem)

    def test_achatar_e_despachado_para_a_segmentacao(self):
        """A barra de efeitos precisa alcancar o metodo do Kruskal."""
        saida = efeito.aplicar("achatar", self.imagem, self.mascara, 10)
        self.assertEqual(saida.shape, self.imagem.shape)
        self.assertIn("achatar", efeito.EFEITOS)

    def test_parametros_invalidos(self):
        with self.assertRaises(ValueError):
            efeito.borrar(self.imagem, self.mascara, raio=0)
        with self.assertRaises(ValueError):
            efeito.pixelizar(self.imagem, self.mascara, bloco=1)
        with self.assertRaises(ValueError):
            efeito.aplicar("inexistente", self.imagem, self.mascara)


if __name__ == "__main__":
    unittest.main(verbosity=2)
