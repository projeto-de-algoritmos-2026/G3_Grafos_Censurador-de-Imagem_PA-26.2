"""Testes do METODO 2 - tesoura por Dijkstra."""

import unittest
from itertools import product

import numpy as np

from apoio import duas_metades, quatro_quadrantes
from core import grafo_imagem, tesoura


def custo_bruto(grade: np.ndarray, inicio, fim) -> float:
    """Menor custo por busca exaustiva, para conferir o Dijkstra.

    Programacao dinamica sobre todos os caminhos simples e caro; aqui a grade
    e minuscula (4x4), entao a forca bruta com poda por custo ja e suficiente
    e, principalmente, e obviamente correta - que e o ponto de um oraculo.
    """
    altura, largura = grade.shape
    melhor = [float("inf")]

    def andar(pos, visitados, acumulado):
        # acumulado NAO inclui o custo do pixel de origem, igual ao Dijkstra
        if acumulado >= melhor[0]:
            return
        if pos == fim:
            melhor[0] = acumulado
            return
        l, c = pos
        for dl, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nl, nc = l + dl, c + dc
            if 0 <= nl < altura and 0 <= nc < largura and (nl, nc) not in visitados:
                andar((nl, nc), visitados | {(nl, nc)}, acumulado + grade[nl, nc])

    andar(inicio, {inicio}, 0.0)
    return melhor[0]


class TestCustoDePixel(unittest.TestCase):
    def test_borda_custa_menos_que_area_lisa(self):
        grafo = grafo_imagem.construir(duas_metades(20, 20))
        custo = tesoura.mapa_de_custo(grafo)
        self.assertLess(custo[10, 10], custo[10, 2])  # sobre a borda x no meio do bloco

    def test_custo_nunca_e_zero(self):
        """Pixel de custo zero permitiria caminhos gratuitos infinitos."""
        grafo = grafo_imagem.construir(quatro_quadrantes(16))
        self.assertGreater(float(tesoura.mapa_de_custo(grafo).min()), 0.0)

    def test_reforco_invalido(self):
        grafo = grafo_imagem.construir(quatro_quadrantes(8))
        with self.assertRaises(ValueError):
            tesoura.mapa_de_custo(grafo, reforco=0)


class TestDijkstra(unittest.TestCase):
    def setUp(self):
        self.grafo = grafo_imagem.construir(quatro_quadrantes(12))

    def test_bate_com_a_busca_exaustiva(self):
        """O otimo do Dijkstra tem que ser o otimo de verdade."""
        grade = np.array([[1.0, 9.0, 9.0, 9.0],
                          [1.0, 1.0, 9.0, 9.0],
                          [9.0, 1.0, 1.0, 9.0],
                          [9.0, 9.0, 1.0, 1.0]])
        grafo = grafo_imagem.construir(np.zeros((4, 4, 3), dtype=np.uint8))
        resultado = tesoura.tracar(grafo, (0, 0), (3, 3), grade)
        # os dois somam o custo dos pixels de CHEGADA, sem cobrar a origem
        esperado = custo_bruto(grade, (0, 0), (3, 3))
        self.assertAlmostEqual(resultado.custo, esperado, places=6)
        self.assertEqual(len(resultado.caminho), 7)  # 6 passos de Manhattan

    def test_caminho_e_contiguo(self):
        resultado = tesoura.tracar(self.grafo, (1, 1), (10, 10))
        self.assertTrue(resultado.sucesso)
        for (l1, c1), (l2, c2) in zip(resultado.caminho, resultado.caminho[1:]):
            self.assertEqual(abs(l1 - l2) + abs(c1 - c2), 1)  # sempre um passo de 4

    def test_extremos_corretos(self):
        resultado = tesoura.tracar(self.grafo, (2, 3), (9, 8))
        self.assertEqual(resultado.caminho[0], (2, 3))
        self.assertEqual(resultado.caminho[-1], (9, 8))

    def test_segue_o_corredor_barato(self):
        """Com um corredor de custo baixo, o caminho tem que preferi-lo."""
        grade = np.full((11, 11), 10.0)
        grade[5, :] = 0.1          # corredor horizontal barato na linha 5
        grade[:, 10] = 0.1         # e uma descida barata na ultima coluna
        grafo = grafo_imagem.construir(np.zeros((11, 11, 3), dtype=np.uint8))
        caminho = tesoura.tracar(grafo, (5, 0), (10, 10), grade).caminho
        na_rota_barata = sum(1 for l, c in caminho if l == 5 or c == 10)
        self.assertGreaterEqual(na_rota_barata, len(caminho) - 1)

    def test_mesmo_ponto(self):
        resultado = tesoura.tracar(self.grafo, (4, 4), (4, 4))
        self.assertTrue(resultado.sucesso)
        self.assertEqual(resultado.custo, 0.0)
        self.assertEqual(resultado.caminho, [(4, 4)])

    def test_simetria_do_custo(self):
        """Ida e volta custam o mesmo a menos do custo dos pontos extremos."""
        ida = tesoura.tracar(self.grafo, (1, 1), (9, 9))
        volta = tesoura.tracar(self.grafo, (9, 9), (1, 1))
        custo = tesoura.mapa_de_custo(self.grafo)
        self.assertAlmostEqual(ida.custo + custo[1, 1],
                               volta.custo + custo[9, 9], places=5)

    def test_ponto_fora_da_imagem(self):
        with self.assertRaises(ValueError):
            tesoura.tracar(self.grafo, (0, 0), (99, 99))

    def test_expande_no_maximo_todos_os_pixels(self):
        resultado = tesoura.tracar(self.grafo, (0, 0), (11, 11))
        self.assertLessEqual(resultado.expandidos, self.grafo.total_vertices)


class TestPoligonal(unittest.TestCase):
    def setUp(self):
        self.grafo = grafo_imagem.construir(quatro_quadrantes(16))

    def test_encadeia_os_trechos_sem_repetir_pixel(self):
        pontos = [(1, 1), (1, 14), (14, 14)]
        total = tesoura.tracar_poligonal(self.grafo, pontos)
        self.assertTrue(total.sucesso)
        self.assertEqual(total.caminho[0], pontos[0])
        self.assertEqual(total.caminho[-1], pontos[-1])
        for (l1, c1), (l2, c2) in zip(total.caminho, total.caminho[1:]):
            self.assertEqual(abs(l1 - l2) + abs(c1 - c2), 1)

    def test_fechar_volta_ao_inicio(self):
        pontos = [(2, 2), (2, 13), (13, 13)]
        fechado = tesoura.tracar_poligonal(self.grafo, pontos, fechar=True)
        self.assertEqual(fechado.caminho[-1], pontos[0])

    def test_exige_dois_pontos(self):
        with self.assertRaises(ValueError):
            tesoura.tracar_poligonal(self.grafo, [(0, 0)])


if __name__ == "__main__":
    unittest.main(verbosity=2)
