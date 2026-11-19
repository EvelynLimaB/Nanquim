# Cores do Nanquim

Paleta do redesenho (patch 0098): grafite e papel, com verdete como único destaque. Cada cor tem um papel só. Patch novo usa estas cores e não inventa outra. No código elas ficam no namespace `Cor` de `libs/ui/NanquimTabletUi.cpp`. Os nomes antigos das constantes (`AZUL`, `CIANO`, `AZUL_CLARO`) ficaram para não mexer no arquivo todo, mas guardam os verdes abaixo.

## Cores com papel

| Cor | Hex | Constante | Papel |
|---|---|---|---|
| Verdete | `#3e8e7e` | `Cor::AZUL` | Ativo, seleção, borda de foco, camada de tinta |
| Verdete escuro | `#2f7568` | | Fundo do botão principal e da ferramenta ativa, sempre com texto branco |
| Verdete claro | `#6fbfad` | `Cor::CIANO`, `Cor::AZUL_CLARO` | Toque, anel do item ativo, arte-final, texto e ícone ativos, barras de progresso |
| Coral | `#ff6b8b` | `Cor::CORAL` | Borracha, erro, ação que apaga |
| Verde | `#5ec98c` | `Cor::VERDE` | Pronto, salvo, concluído |
| Âmbar | `#e6b45a` | `Cor::AMBAR` | Rascunho, atenção |

Sem degradê de um matiz para outro. A logo é a exceção: a gota vai de `#2f7568` a `#6fbfad`.

## Neutros

| Nome | Hex | Uso |
|---|---|---|
| Grafite | `#24231f` | Fundo do app e em volta da página |
| Superfície | `#2e2d29` | Painéis, cartões, peças flutuantes |
| Superfície 2 | `#3a3934` | Item pressionado ou escolhido dentro de um painel |
| Linha | `#4a4842` | Bordas, trilhos, separadores |
| Papel | `#f3eee3` | Página creme, fundo das amostras de traço |
| Texto | `#eeeae0` | Texto principal |
| Texto suave | `#a8a398` | Legendas e informações |

## Relevo

Superfícies lisas, sem brilho no topo. O que muda entre os níveis é a borda.

| Nível | Onde | Fundo | Borda |
|---|---|---|---|
| 1 | Barras fixas | `#2e2d29` | `#4a4842` |
| 2 | Peças sobre a página | `rgba(46,45,41,0.96)` | `#524f48` |
| 3 | Pop-ups e janelas | `#2e2d29` | `#5a574f` |

No código: `NQ_RELEVO2_BG`, `NQ_RELEVO2_BORDA`, `NQ_RELEVO3_BG`, `NQ_RELEVO3_BORDA`.
