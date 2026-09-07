# Segmentador — ferramenta de seleção e censura de imagens

Trata uma imagem como um **grafo em grade**: cada pixel é um vértice, cada par
de pixels adjacentes é uma aresta, e o peso é a diferença de cor entre eles.
Sobre essa mesma estrutura rodam dois algoritmos clássicos, cada um resolvendo
um problema real de edição de imagem.

**O que o programa faz, na prática:** você seleciona uma área por um dos três
caminhos e aplica desfoque, mosaico ou tarja preta apenas nela. É uma
ferramenta de censura de imagem — rosto, placa de carro, documento.

| Método | Algoritmo | O que faz | É isso em ferramenta comercial |
|---|---|---|---|
| 1 | **Kruskal** | agrupa pixels em regiões de cor coerente | segmentação automática |
| 2 | **Dijkstra** | traça o contorno de um objeto entre dois cliques | laço magnético / tesoura inteligente |
| extra | flood fill | seleciona a região conectada de cor parecida | varinha mágica |

O flood fill **não conta como método**: é busca em largura simples, sem custo
acumulado nem decisão de otimalidade. Está no projeto por dois motivos. O
primeiro é de contraste: percorre por semelhança de cor, enquanto Dijkstra
percorre minimizando custo acumulado e Kruskal nem percorre, apenas ordena
arestas e funde regiões. O segundo é funcional — **é ele que preenche o
interior do contorno traçado pelo Dijkstra**, como se explica abaixo.

## O que unifica os três: a máscara

O Dijkstra devolve um *contorno* (uma linha de pixels), o Kruskal devolve
*rótulos* (a que região cada pixel pertence) e o flood fill devolve uma
*região conectada*. Coisas diferentes — mas todas se reduzem a uma **máscara
booleana** do tamanho da imagem, e o efeito se aplica a qualquer uma delas sem
saber quem a produziu.

Na interface, cada painel implementa `mascara_atual()`; a barra de efeitos
consome o resultado do painel ativo. É esse contrato que faz o programa ser
uma ferramenta só, em vez de três demonstrações soltas.

| Aba | Como selecionar | Máscara resultante |
|---|---|---|
| Kruskal | segmentar e clicar nas regiões (clicar de novo desmarca) | união das regiões marcadas |
| Dijkstra | marcar pontos ao redor do objeto com *Fechar o contorno* ligado | interior da área contornada |
| Flood fill | clicar em um ponto | região conectada de cor parecida |

### O contorno vira área por flood fill invertido

`efeito.interior_do_contorno` não inunda a área desejada: inunda tudo o que
está **fora** dela, partindo das bordas da imagem e tratando o contorno como
parede. O que a inundação não alcançou é o interior. Nenhuma comparação de cor
acontece aí, só conectividade — por isso funciona mesmo quando o interior é
todo colorido e variado.

Se o contorno não estiver fechado, a inundação contorna o traço e alcança os
dois lados dele; não sobra interior algum além da própria parede, e a função
devolve máscara vazia em vez de uma seleção sem sentido. O teste
`test_contorno_aberto_nao_gera_area` cobre esse caso.

### Efeitos

Quatro opções, sendo a primeira a mais interessante do ponto de vista do
trabalho:

**Achatar (Kruskal)** — a própria segmentação usada como efeito. Os pixels da
área são agrupados em regiões e cada região é pintada com a sua cor média. O
detalhe some, mas as formas grandes e a paleta permanecem: o resultado parece
pintura, não mosaico. O parâmetro de intensidade vira a escala `k`: valores
baixos preservam as formas do rosto, valores altos achatam tudo em poucas
manchas. É o único efeito aqui que **é um algoritmo de grafo**, e não um filtro
de convolução — e como a informação dentro de cada região é substituída por um
único valor, não há o que reverter, ao contrário do desfoque, que é operação
linear e pode ser parcialmente desfeito.

Por rodar apenas no retângulo que envolve a máscara, custa cerca de 0,2 s numa
seleção do tamanho de um rosto, em vez dos 2,2 s de segmentar a imagem inteira.

Um detalhe que vale entender: sobre uma área de **cor chapada**, achatar não
muda nada, porque a média da região é a própria cor. Não é defeito — é a
diferença entre achatar por segmentação e filtrar. O teste
`test_achatar_preserva_area_ja_chapada` documenta isso.

**Borrar** (gaussiano), **pixelizar** (mosaico) e **tarjar** (preto) completam o
conjunto. O desfoque é calculado na imagem inteira e depois recortado pela
máscara — borrar apenas os pixels selecionados deixaria a borda dura e
denunciaria o recorte.

Aplicar um efeito **reconstrói o grafo**, para que uma segmentação ou contorno
calculados depois enxerguem a imagem como ela está agora. Há pilha de desfazer
e exportação em PNG/JPEG.

## Como executar

```bash
pip install numpy pillow
python main.py                # interface com a imagem de exemplo
python main.py foto.jpg       # interface com uma imagem sua
python main.py --demo         # gera resultado.png com o painel comparativo
python main.py --benchmark    # mede tempo por número de pixels
python -m unittest discover -s tests -t tests -v
```

No Linux, se `import tkinter` falhar: `sudo apt install python3-tk`.

## Divisão do trabalho

Os dois métodos são independentes: nenhum importa o outro, e cada um tem seu
módulo de núcleo, seu painel de interface e seu arquivo de testes. Os dois
integrantes podem trabalhar em paralelo sem conflito de merge.

| Arquivo | Dono | Conteúdo |
|---|---|---|
| `core/grafo_imagem.py` | **base** | estrutura do grafo, carga da imagem |
| `core/efeito.py` | **base** | máscara a partir de contorno, desfoque/mosaico/tarja |
| `core/union_find.py` | **base** | conjuntos disjuntos |
| `gui/app.py`, `gui/pintura.py`, `gui/tarefa.py` | **base** | janela, canvas, sobreposições, thread |
| `tests/test_grafo_imagem.py`, `tests/test_efeito.py` | **base** | testes da estrutura e dos efeitos |
| `core/segmentacao.py` | **A** | Kruskal com critério de fusão e efeito de achatamento |
| `gui/painel_segmentacao.py` | **A** | aba do método 1 |
| `tests/test_segmentacao.py` | **A** | testes do método 1 |
| `core/tesoura.py` | **B** | Dijkstra sobre o mapa de custo |
| `gui/painel_tesoura.py` | **B** | aba do método 2 |
| `tests/test_tesoura.py` | **B** | testes do método 2 |
| `core/selecao.py`, `gui/painel_selecao.py`, `tests/test_selecao.py` | qualquer um | flood fill (extra) |

**A base precisa ser commitada primeiro**, porque os dois lados dependem dela.
Depois disso, A e B não tocam nos mesmos arquivos.

Cada painel conversa com a janela por um contrato de cinco métodos —
`ao_clicar`, `ao_ativar`, `ao_trocar_imagem`, `redesenhar` e `mascara_atual` —
e nunca importa o outro painel. Adicionar um terceiro método é escrever um painel novo e
registrá-lo em `_montar_abas`.

## Método 1 — Kruskal aplicado à segmentação

É o mesmo Kruskal da árvore geradora mínima: percorre as arestas da mais
barata para a mais cara e usa union-find para decidir a fusão. A diferença é
que, em vez de aceitar toda aresta que não forma ciclo, aplica um critério de
parada (Felzenszwalb & Huttenlocher, 2004). Duas regiões só se fundem se a
aresta que as separa for mais barata que a variação de cor que cada uma já
tolera internamente:

```
peso ≤ min( Int(A) + k/|A| , Int(B) + k/|B| )
```

`Int(C)` é a maior aresta interna da região — a maior diferença de cor que ela
já aceitou. O termo `k/|C|` dá escala ao resultado: região pequena se funde com
facilidade, região já grande exige evidência forte para crescer. Sem ele, uma
única aresta barata colaria dois objetos grandes por um ponto de contato.

**Se todas as arestas fossem aceitas, o resultado seria a AGM da imagem
inteira: uma única região.** O critério é exatamente o que transforma árvore
geradora mínima em segmentação.

Uma segunda passada absorve regiões abaixo de `tamanho_minimo`, porque ruído
de sensor gera muitas regiões de poucos pixels que não representam nada.

## Método 2 — Dijkstra aplicado à tesoura inteligente

O usuário clica ao redor do objeto e cada trecho entre dois cliques é um
Dijkstra independente. O truque está no custo: aqui o peso não está na aresta
e sim **no pixel de chegada** — atravessar um pixel de borda é barato,
atravessar área lisa é caro. Como Dijkstra minimiza custo acumulado, o caminho
mais barato entre dois cliques é o que passa o maior tempo possível sobre
bordas, ou seja, contornando o objeto.

O custo por pixel vem da magnitude do gradiente (diferenças centrais escritas à
mão). Um piso de custo é somado para que nenhum pixel custe zero — caso
contrário surgiriam caminhos gratuitos arbitrariamente longos ao longo de uma
mesma borda.

Cada pixel é fechado na primeira retirada da fila: como todos os custos são
positivos, nenhuma retirada posterior poderia melhorá-lo. Entradas obsoletas
são descartadas na saída, o que dispensa a operação de *decrease-key*.

## Complexidade e desempenho medido

Uma imagem H×L tem `H·L` vértices e `2·H·L − H − L` arestas.

| Algoritmo | Estrutura | Complexidade |
|---|---|---|
| Kruskal | Union-Find (compressão de caminho + união por rank) | O(E log E), dominado pela ordenação |
| Dijkstra | Fila de prioridade (`heapq`) | O(E log V) |
| flood fill | Fila (BFS) | O(V + E) |
| preenchimento do contorno | Fila (BFS invertida) | O(V + E) |

Medição real (`--benchmark`, imagem de exemplo redimensionada):

| lado | vértices | arestas | Kruskal | Dijkstra |
|---|---|---|---|---|
| 64 | 4.096 | 8.064 | 0,041 s | 0,015 s |
| 128 | 16.384 | 32.512 | 0,139 s | 0,056 s |
| 256 | 65.536 | 130.560 | 0,553 s | 0,244 s |
| 512 | 262.144 | 523.264 | 2,226 s | 1,348 s |

Dobrar o lado quadruplica os vértices e o tempo cresce por volta de 4×, o que é
o esperado: o fator `log` cresce devagar demais para aparecer nessa faixa.

Duas decisões de implementação sustentam esse desempenho em Python puro:

1. **Pesos e ordenação em numpy.** Só ficam em laço Python as etapas em que a
   ordem de processamento importa — o union-find do Kruskal e a fila do
   Dijkstra, que são inerentemente sequenciais.
2. **Redução da imagem para 512 px de lado** ao carregar. Não altera o
   comportamento dos algoritmos, só mantém a interface responsiva.

A segmentação roda em uma **thread separada** (`gui/tarefa.py`), com a interface
consultando o resultado por `after()`. Sem isso a janela congelaria por
segundos e pareceria travada. Widgets Tkinter não podem ser tocados de outra
thread, e é por isso que o retorno passa pelo `after()`.

## Testes

56 testes, executados com `python -m unittest discover -s tests -t tests`.

Os testes usam **imagens sintéticas** (duas metades, quatro quadrantes, ruído
com semente fixa) em vez de fotos, porque assim a resposta certa é conhecida de
antemão. Destaques:

- `test_regioes_sao_conexas` — Kruskal só funde vizinhos, então nenhuma região
  pode ficar partida; verificado por varredura em largura em cada região.
- `test_contabilidade_das_arestas` — toda aresta cai em exatamente um destino:
  fusão, ciclo, ou reprovada pelo critério. A soma tem que fechar com `E`.
- `test_k_maior_produz_menos_regioes` — propriedade central do parâmetro de
  escala, verificada em quatro valores.
- `test_bate_com_a_busca_exaustiva` — o custo do Dijkstra é comparado com uma
  busca exaustiva sobre uma grade 4×4. O oráculo é obviamente correto por ser
  força bruta, que é o ponto de usar um.
- `test_caminho_e_contiguo` — passos sempre de vizinhança 4, sem saltos.
- `test_regiao_desconexa_nao_e_incluida` — duas áreas da mesma cor separadas:
  o flood fill só pode pegar a conectada.
- `test_efeito_nao_altera_fora_da_mascara` — requisito central da ferramenta:
  o resto da foto tem que ficar byte a byte intacto.
- `test_quadrado_fechado_preenche_o_interior` — um contorno 10×10 desenhado à
  mão precisa virar exatamente 100 px de área.
- `test_k_maior_achata_mais` — a intensidade do achatamento tem que ser
  monotônica na escala `k`.

## Imagem de exemplo

`dados/exemplo.png` é a fotografia da astronauta Eileen Collins, do banco de
imagens da NASA, em **domínio público**. Qualquer imagem própria pode ser
aberta pelo botão *Abrir imagem*.

## Referência

Felzenszwalb, P. F.; Huttenlocher, D. P. *Efficient Graph-Based Image
Segmentation*. International Journal of Computer Vision, v. 59, n. 2, 2004.
