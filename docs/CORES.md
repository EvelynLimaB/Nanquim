# Cores do Nanquim

Cada cor tem um papel só. Patch novo usa estas cores e não inventa outra. No código elas ficam no namespace `Cor` de `libs/ui/NanquimTabletUi.cpp` (patch 0086).

## Cores com papel

| Cor | Hex | Papel |
|---|---|---|
| Azul | `#3d8bff` | Ativo, seleção, borda de foco, botão principal, camada de tinta |
| Ciano | `#22d3ee` | Toque, ferramenta ativa, trabalho em andamento, arte-final, retícula |
| Coral | `#ff6b8b` | Borracha, erro, ação que apaga |
| Verde | `#5ec98c` | Pronto, salvo, concluído |
| Âmbar | `#e6b45a` | Rascunho, atenção |
| Azul claro | `#6aa6ff` | Texto e ícone ativos, números de medida, camada vetorial e de texto |

O degradê de destaque vai de ciano para azul (`#22d3ee` → `#3d8bff`). O de progresso vai de azul para verde (`#3d8bff` → `#5ec98c`).

## Neutros

| Nome | Hex | Uso |
|---|---|---|
| Fundo | `#15171b` | Fundo de toda peça da interface |
| Linha | `#2a2e35` | Bordas do nível 1, trilhos, separadores |
| Texto | `#eceef2` | Texto principal |
| Texto suave | `#a4a9b3` | Legendas e informações |

## Três níveis de relevo

Quanto mais perto do dedo, mais brilho no topo e mais clara a borda. O fundo é sempre `#15171b`, para o conteúdo combinar.

| Nível | Onde | Topo | Borda |
|---|---|---|---|
| 1 | Barras fixas (topo, lateral) | plano | `#2a2e35` |
| 2 | Peças sobre a página (dock, cores rápidas, cápsula, cartões) | `rgba(34,38,44,0.96)` até 22% | `#33373f` |
| 3 | Pop-ups e janelas (painéis, pincéis, ferramentas, avisos) | `#272b33` até 14% | `#3f4551` |

No código: `NQ_RELEVO2_BG`, `NQ_RELEVO2_BORDA`, `NQ_RELEVO3_BG`, `NQ_RELEVO3_BORDA`.
