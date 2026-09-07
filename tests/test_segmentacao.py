"""Testes do METODO 1 - segmentacao por Kruskal."""

import unittest

import numpy as np

from apoio import duas_metades, quatro_quadrantes, ruido
from core import grafo_imagem, segmentacao


class TestSegmentacao(unittest.TestCase):
    def test_duas_metades_viram_duas_regioes(self):
        grafo = grafo_imagem.construir(duas_metades(20, 20))
        resultado = segmentacao.segmentar(grafo, k=100, tamanho_minimo=1)
        self.assertEqual(resultado.total_regioes, 2)

    def test_quatro_quadrantes_viram_quatro_regioes(self):
        grafo = grafo_imagem.construir(quatro_quadrantes(20))
        resultado = segmentacao.segmentar(grafo, k=100, tamanho_minimo=1)
        self.assertEqual(resultado.total_regioes, 4)

    def test_regiao_corresponde_ao_quadrante(self):
        """Os rotulos precisam bater com a geometria real da imagem."""
        grafo = grafo_imagem.construir(quatro_quadrantes(20))
        rotulos = segmentacao.segmentar(grafo, k=100, tamanho_minimo=1).rotulos
        self.assertEqual(len(np.unique(rotulos[:10, :10])), 1)
        self.assertNotEqual(rotulos[0, 0], rotulos[0, 19])
        self.assertNotEqual(rotulos[0, 0], rotulos[19, 0])

    def test_k_maior_produz_menos_regioes(self):
        """Propriedade central do parametro de escala."""
        grafo = grafo_imagem.construir(ruido(40, 40))
        anterior = None
        for k in (50, 500, 5000, 50000):
            atual = segmentacao.segmentar(grafo, k=k, tamanho_minimo=1).total_regioes
            if anterior is not None:
                self.assertLessEqual(atual, anterior, f"k={k} deveria unir mais")
            anterior = atual

    def test_todo_pixel_recebe_rotulo(self):
        grafo = grafo_imagem.construir(quatro_quadrantes(16))
        rotulos = segmentacao.segmentar(grafo).rotulos
        self.assertEqual(rotulos.shape, (16, 16))
        self.assertFalse(np.any(rotulos < 0))

    def test_regioes_sao_conexas(self):
        """Kruskal so funde vizinhos, logo nenhuma regiao pode ficar partida."""
        grafo = grafo_imagem.construir(quatro_quadrantes(16))
        rotulos = segmentacao.segmentar(grafo, k=100, tamanho_minimo=1).rotulos
        for rotulo in np.unique(rotulos):
            mascara = rotulos == rotulo
            # varredura em largura a partir do primeiro pixel da regiao
            inicio = tuple(np.argwhere(mascara)[0])
            visto = np.zeros_like(mascara)
            pilha = [inicio]
            visto[inicio] = True
            while pilha:
                l, c = pilha.pop()
                for dl, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nl, nc = l + dl, c + dc
                    if (0 <= nl < mascara.shape[0] and 0 <= nc < mascara.shape[1]
                            and mascara[nl, nc] and not visto[nl, nc]):
                        visto[nl, nc] = True
                        pilha.append((nl, nc))
            self.assertEqual(int(visto.sum()), int(mascara.sum()),
                             f"a regiao {rotulo} ficou partida")

    def test_tamanho_minimo_elimina_regioes_pequenas(self):
        grafo = grafo_imagem.construir(ruido(40, 40))
        sem_limite = segmentacao.segmentar(grafo, k=50, tamanho_minimo=1)
        com_limite = segmentacao.segmentar(grafo, k=50, tamanho_minimo=100)
        self.assertLess(com_limite.total_regioes, sem_limite.total_regioes)

    def test_contabilidade_das_arestas(self):
        """Toda aresta cai em exatamente um dos tres destinos possiveis."""
        grafo = grafo_imagem.construir(quatro_quadrantes(12))
        r = segmentacao.segmentar(grafo, tamanho_minimo=1)
        self.assertEqual(r.fusoes + r.descartes_ciclo + r.descartes_criterio,
                         grafo.total_arestas)

    def test_resultado_e_deterministico(self):
        grafo = grafo_imagem.construir(ruido(30, 30))
        primeira = segmentacao.segmentar(grafo, k=300).rotulos
        segunda = segmentacao.segmentar(grafo, k=300).rotulos
        np.testing.assert_array_equal(primeira, segunda)

    def test_parametro_invalido(self):
        grafo = grafo_imagem.construir(quatro_quadrantes(8))
        with self.assertRaises(ValueError):
            segmentacao.segmentar(grafo, k=0)


class TestAchatamento(unittest.TestCase):
    """A segmentacao usada como efeito sobre uma area selecionada."""

    def setUp(self):
        self.imagem = ruido(60, 60)
        self.mascara = np.zeros((60, 60), dtype=bool)
        self.mascara[20:40, 20:40] = True

    def test_nao_altera_fora_da_mascara(self):
        saida = segmentacao.achatar(self.imagem, self.mascara, k=1500)
        np.testing.assert_array_equal(saida[~self.mascara], self.imagem[~self.mascara])

    def test_reduz_a_quantidade_de_cores_na_area(self):
        """Achatar troca o detalhe por manchas: menos cores distintas."""
        saida = segmentacao.achatar(self.imagem, self.mascara, k=3000)
        antes = len(np.unique(self.imagem[self.mascara], axis=0))
        depois = len(np.unique(saida[self.mascara], axis=0))
        self.assertLess(depois, antes)

    def test_k_maior_achata_mais(self):
        cores = []
        for k in (300, 3000, 30000):
            saida = segmentacao.achatar(self.imagem, self.mascara, k=k)
            cores.append(len(np.unique(saida[self.mascara], axis=0)))
        self.assertGreaterEqual(cores[0], cores[1])
        self.assertGreaterEqual(cores[1], cores[2])

    def test_mascara_vazia_devolve_copia(self):
        vazia = np.zeros((60, 60), dtype=bool)
        np.testing.assert_array_equal(
            segmentacao.achatar(self.imagem, vazia), self.imagem)

    def test_area_minuscula_nao_quebra(self):
        """Uma selecao de 1 px nao forma grafo: retorna a imagem intacta."""
        pontual = np.zeros((60, 60), dtype=bool)
        pontual[30, 30] = True
        np.testing.assert_array_equal(
            segmentacao.achatar(self.imagem, pontual), self.imagem)


class TestApoioVisual(unittest.TestCase):
    def test_cor_media_preserva_a_forma(self):
        imagem = quatro_quadrantes(20)
        grafo = grafo_imagem.construir(imagem)
        rotulos = segmentacao.segmentar(grafo, k=100, tamanho_minimo=1).rotulos
        media = segmentacao.cor_media(imagem, rotulos)
        self.assertEqual(media.shape, imagem.shape)
        # em blocos de cor uniforme, a media reproduz a cor original
        np.testing.assert_allclose(media[0, 0], imagem[0, 0], atol=1)

    def test_contornos_marcam_as_fronteiras(self):
        grafo = grafo_imagem.construir(duas_metades(10, 10))
        rotulos = segmentacao.segmentar(grafo, k=100, tamanho_minimo=1).rotulos
        borda = segmentacao.contornos(rotulos)
        self.assertTrue(borda[:, 4].all())      # coluna anterior a troca
        self.assertFalse(borda[:, 0].any())     # interior da regiao


if __name__ == "__main__":
    unittest.main(verbosity=2)
