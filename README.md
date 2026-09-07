# Censura Inteligente de Imagens

**Conteúdo da Disciplina**: Grafos<br>

## Alunos

Link para a gravação: https://www.youtube.com/watch?v=OYGQycu4kFw

| Matrícula | Aluno |
| -- | -- |
| 232003661  | João Pedro Araújo de Freitas Lyra |
| 222033952 | Cristiano Borges de Morais |

## Sobre

Uma ferramenta de seleção e censura de imagens construída inteiramente sobre
algoritmos de grafos.

A ideia central é tratar a imagem como um **grafo em grade**: cada pixel é um
vértice, cada par de pixels vizinhos é uma aresta, e o peso da aresta é a
diferença de cor entre eles. Uma foto 512×512 vira um grafo de 262.144 vértices
e 523.264 arestas. Sobre essa mesma estrutura rodam os dois métodos do
trabalho, cada um resolvendo um problema real de edição de imagem:

| Método | Algoritmo | O que faz | Equivalente comercial |
| -- | -- | -- | -- |
| 1 | **Kruskal** | agrupa os pixels em regiões de cor coerente | segmentação automática |
| 2 | **Dijkstra** | traça o contorno de um objeto entre dois cliques | laço magnético / tesoura inteligente |
| extra | flood fill | seleciona a região conectada de cor parecida | varinha mágica |

**Como os três se encaixam.** Eles produzem coisas diferentes — o Kruskal
devolve rótulos, o Dijkstra devolve uma linha de pixels, o flood fill devolve
uma região — mas todos se reduzem a uma **máscara booleana** do tamanho da
imagem. O efeito escolhido é então aplicado só dentro dessa máscara, sem saber
qual algoritmo a produziu. É isso que faz o programa ser uma ferramenta única
em vez de três demonstrações soltas.

O flood fill ainda tem um segundo papel, funcional: é ele que **preenche o
interior do contorno traçado pelo Dijkstra**. O preenchimento é feito de forma
invertida — inunda tudo o que está *fora*, partindo das bordas da imagem e
tratando o contorno como parede; o que a inundação não alcançou é o interior.
Como não há comparação de cor nenhuma nesse passo, funciona mesmo quando o
interior é todo variado.

**Os efeitos** são quatro: achatar, borrar, pixelizar e tarjar. O primeiro é o
mais relevante para a disciplina, porque **é o próprio Kruskal usado como
efeito**: a área selecionada é segmentada e cada região é pintada com a sua cor
média. O resultado parece pintura, não mosaico. Como censura, tem vantagem
sobre o desfoque gaussiano — o desfoque é uma operação linear e pode ser
parcialmente revertido, enquanto aqui a informação dentro de cada região é
substituída por um único valor e não há o que reverter.

## Screenshots

**1. Kruskal — segmentação da imagem em regiões**
Os contornos em laranja são as fronteiras encontradas pelo algoritmo, usando
apenas a diferença de cor entre pixels vizinhos.

![Segmentação por Kruskal](docs/01-kruskal-segmentacao.png)

**2. Dijkstra + achatamento — o caso de uso de censura**
O contorno do rosto foi traçado com quatro cliques, o interior foi preenchido e
o efeito de achatamento por Kruskal foi aplicado apenas nessa área.

![Contorno por Dijkstra e achatamento](docs/02-dijkstra-achatamento.png)

**3. Flood fill — seleção por região conectada**
Clique único seleciona a área contígua de cor parecida, respeitando a
tolerância informada.

![Flood fill](docs/03-flood-fill.png)

**4. Comparação dos efeitos**
Da esquerda para a direita: original, achatamento com k baixo, achatamento com
k alto, desfoque gaussiano e mosaico. O achatamento preserva as formas e a
paleta; o mosaico impõe uma grade quadrada.

![Comparação dos efeitos](docs/04-comparacao-efeitos.png)

## Instalação

**Linguagem**: Python 3.10 ou superior<br>
**Framework**: nenhum. A interface usa Tkinter, que faz parte da biblioteca
padrão. As únicas dependências externas são NumPy (cálculo vetorizado dos pesos
das arestas) e Pillow (leitura e gravação de imagens).<br>

```bash
git clone <url-do-repositorio>
cd <pasta-do-repositorio>
pip install -r requirements.txt
python main.py
```

No Linux, se aparecer `ModuleNotFoundError: No module named 'tkinter'`:

```bash
sudo apt install python3-tk
```

Para rodar os testes:

```bash
python -m unittest discover -s tests -t tests -v
```
## Uso

Ao abrir, o programa já carrega uma imagem de exemplo. Use **Abrir imagem** para
escolher outra (a imagem é reduzida para no máximo 512 px de lado, para manter a
interface responsiva).

O painel da direita tem uma aba por algoritmo. Selecione a área por um dos três
caminhos e depois aplique o efeito na barra inferior.

**Aba Kruskal**
1. Ajuste `k` (escala das regiões) e o tamanho mínimo, se quiser.
2. Clique em **Segmentar** e aguarde — a barra superior mostra o andamento.
3. Escolha a exibição: contornos sobre a foto ou regiões pela cor média.
4. **Clique nas regiões da imagem** para marcá-las. Clicar de novo desmarca.

**Aba Dijkstra**
1. Deixe **Fechar o contorno** ligado (necessário para selecionar área).
2. Clique em três ou mais pontos ao redor do objeto. Cada trecho entre dois
   cliques é calculado na hora e segue as bordas da imagem.
3. A área interna aparece destacada. Se aparecer "contorno sem área interna",
   adicione mais pontos.
4. **Desfazer ponto** remove o último clique; **Limpar** recomeça.
5. **Ver o mapa de custo** mostra como o algoritmo enxerga a imagem: escuro é
   barato (borda), claro é caro (área lisa).

**Aba Flood fill**
1. Clique em qualquer ponto da imagem.
2. Ajuste a tolerância de cor e clique em **Recalcular** para refinar.

**Barra de efeitos** (parte inferior, vale para qualquer aba)
1. Escolha o efeito: Achatar (Kruskal), Borrar, Pixelizar ou Tarja preta.
2. Ajuste a intensidade. Para o achatamento, a intensidade é a escala das
   manchas: valores baixos preservam as formas, valores altos achatam mais.
3. **Aplicar**. O efeito atinge somente a área selecionada na aba ativa.
4. **Desfazer** volta ao estado anterior; **Salvar imagem** exporta em PNG ou
   JPEG.

Os efeitos são cumulativos e o grafo é reconstruído a cada aplicação, então é
possível segmentar novamente já com a imagem editada.

## Outros

**Divisão do trabalho.** Os dois métodos são independentes: cada um tem seu
módulo de núcleo, seu painel de interface e seu arquivo de testes, e nenhum
importa o outro.

| Arquivo | Responsável | Conteúdo |
| -- | -- | -- |
| `core/grafo_imagem.py`, `core/union_find.py` | base | estrutura do grafo e conjuntos disjuntos |
| `core/efeito.py`, `gui/app.py`, `gui/pintura.py`, `gui/tarefa.py` | base | máscaras, efeitos, janela e execução em thread |
| `core/segmentacao.py`, `gui/painel_segmentacao.py`, `tests/test_segmentacao.py` | método 1 | Kruskal e achatamento |
| `core/tesoura.py`, `gui/painel_tesoura.py`, `tests/test_tesoura.py` | método 2 | Dijkstra e mapa de custo |
| `core/selecao.py`, `gui/painel_selecao.py`, `tests/test_selecao.py` | extra | flood fill |

**Complexidade e desempenho.** Uma imagem H×L tem `H·L` vértices e
`2·H·L − H − L` arestas.

| Algoritmo | Estrutura de apoio | Complexidade |
| -- | -- | -- |
| Kruskal | Union-Find (compressão de caminho + união por rank) | O(E log E), dominado pela ordenação |
| Dijkstra | Fila de prioridade (`heapq`) | O(E log V) |
| flood fill | Fila (BFS) | O(V + E) |

Medição real com `python main.py --benchmark`:

| lado | vértices | arestas | Kruskal | Dijkstra |
| -- | -- | -- | -- | -- |
| 64 | 4.096 | 8.064 | 0,041 s | 0,015 s |
| 128 | 16.384 | 32.512 | 0,139 s | 0,056 s |
| 256 | 65.536 | 130.560 | 0,553 s | 0,244 s |
| 512 | 262.144 | 523.264 | 2,226 s | 1,348 s |

Dobrar o lado quadruplica os vértices e o tempo cresce por volta de 4×, como
esperado — o fator logarítmico cresce devagar demais para aparecer nessa faixa.

**Testes.** São 56 testes, sobre imagens sintéticas (duas metades, quatro
quadrantes, ruído com semente fixa) em vez de fotos, porque assim a resposta
certa é conhecida de antemão. O custo do Dijkstra é conferido contra uma busca
exaustiva numa grade 4×4, e a segmentação é verificada quanto à conexidade de
cada região e à contabilidade das arestas (fusões + ciclos + reprovadas tem que
fechar exatamente com E).

**Outros comandos.**

```bash
python main.py foto.jpg     # abre uma imagem específica
python main.py --demo       # gera resultado.png com um painel comparativo
python main.py --benchmark  # mede tempo por número de pixels
```

**Imagem de exemplo.** `dados/exemplo.png` é a fotografia da astronauta Eileen
Collins, do banco de imagens da NASA, em domínio público.

**Documentação técnica detalhada**: [docs/DETALHES-TECNICOS.md](docs/DETALHES-TECNICOS.md),
com a explicação do critério de fusão do Kruskal, do modelo de custo do
Dijkstra e das decisões de implementação.

**Referência.** FELZENSZWALB, P. F.; HUTTENLOCHER, D. P. *Efficient Graph-Based
Image Segmentation*. International Journal of Computer Vision, v. 59, n. 2,
2004.

