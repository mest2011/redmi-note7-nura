# Créditos

Este repositório junta trabalho de muita gente. O que é deste repositório é pouco: o
driver mínimo do MAX98937, as ligações na árvore do lavender, a saída `Speaker` do UCM,
o serviço de troca de saída, o patch `0001` do Wi-Fi para o 7.2, os patches `0003` a `0007` das
câmeras para o 7.2 (correções do `camss`, os drivers gerados dos sensores e a árvore), o
`libcamera/af-0011`, os ajustes de cor das câmeras e a documentação. O resto vem dos projetos
abaixo.

## Patches de terceiros incluídos

| Arquivo | Autor | Origem |
| --- | --- | --- |
| `kernel/0002-a5xx-reset-ao-retomar.patch` | Fabricio Akio | [`sdm660-mainline/linux@be8062b9b02a`](https://github.com/sdm660-mainline/linux/commit/be8062b9b02a) |
| `kernel/0003-a5xx-latencia-cpu.patch` | Fabricio Akio | [`sdm660-mainline/linux@b63149ee8311`](https://github.com/sdm660-mainline/linux/commit/b63149ee8311) |
| `kernel/0004-a5xx-wptr-sob-trava.patch` | Fabricio Akio | [`sdm660-mainline/linux@45b54a7c4c87`](https://github.com/sdm660-mainline/linux/commit/45b54a7c4c87), enviado à [lista do kernel](https://lore.kernel.org/r/20261031-a5xx-wptr-lock-v1-1-fa7d7b9a7fbe@gmail.com) |
| `libcamera/af-0003` a `af-0010` | Milan Zamazal (Red Hat) | Série RFC ["Autofocus basics for software ISP" v2](https://patchwork.libcamera.org/project/libcamera/list/?series=6324), lista do libcamera, outubro de 2026 |

Os três patches da GPU estão como no fork, sem alteração no conteúdo, com o `Signed-off-by`
original. São eles que corrigem o freeze da GPU. O nome do arquivo foi traduzido; o assunto do
commit não. A série do `libcamera` está como foi enviada à lista, aplicada sobre a v0.8.0 do
pacote do Nura, também com o `Signed-off-by` original. O algoritmo que ela leva ao ISP por
software é o autofoco do IPU3 que já existia no `libcamera`.

## Base de que este trabalho depende

- **[sdm660-mainline](https://github.com/sdm660-mainline):** o kernel mainline do SDM660
  (tag `v7.0.14-sdm660`), o U-Boot que sobe o Nura pela `recovery` (`v2026.10-sdm660`) e o
  `alsa-ucm-conf` do SDM660. Obrigado aos mantenedores e contribuidores.
- **Nickolay Goppen**, pelo branch `upstream-sm8250` do `alsa-ucm-conf` do sdm660-mainline, que
  adapta o UCM aos nomes do kernel 7.2 e hoje está no `master`. A saída `Speaker` do 7.2 foi
  escrita sobre ele.
- **Franco Ortiz** ([Pakvothe](https://github.com/Pakvothe)), pelo mapa de registradores do
  MAX98937 dentro do driver `max98927` (branch
  [`lavender-7.2.y`](https://github.com/Pakvothe/linux/tree/lavender-7.2.y)). A proposta da
  caixa para o 7.2 usa os patches dele, com a autoria mantida.
- **SudosuBash**, pelo comentário na issue
  [sdm660-mainline/linux#243](https://github.com/sdm660-mainline/linux/issues/243) que aponta
  o TXBF zerado depois do `vdev down` como causa de queda do firmware do WCN3990. O patch do
  Wi-Fi parte dessa pista.
- **Shunsuke Nagashima**, pela série
  ["wifi: ath10k: WCN3990 station fixes for PMF and failed connections"](https://lkml.iu.edu/2610.1/19749.html):
  foi ele quem achou que, sem a flag de PMF no peer, o firmware do WCN3990 não agrega quadros.
  O `kernel-7.2/0002` é a correção do patch 1/3 dele, adaptada para não mudar o formato da
  `struct ath10k`. O projeto [ROCKNIX](https://github.com/ROCKNIX/distribution/pull/3613)
  documentou o mesmo sintoma.
- **Câmeras:** o modelo dos drivers dos sensores segue a estrutura do `s5kjn1.c` (Linaro) do
  kernel. As sequências de registradores, as ligações das câmeras e os valores do motor de foco
  vêm das bibliotecas e do device tree do MIUI da Xiaomi para o lavender, que não fazem parte
  deste repositório. O driver `dw9719` do kernel, com suporte ao DW9800K, é usado como está.
- **[libcamera](https://libcamera.org)**: o pipeline `simple`, o ISP por software e o pacote
  `temp/libcamera` do pmaports (mantido por Robert Mader), sobre o qual os patches de autofoco
  são aplicados.
- **Árvore do Redmi Note 6 Pro (`tulip`)** no sdm660-mainline: serviu de modelo para a
  ligação `PRI_MI2S`, os pinos e o regulador do amplificador.
- **[Nura](https://nura.eco)** (ex-postmarketOS): o sistema, o `pmbootstrap` e o
  `pmaports`. Os pacotes alterados aqui são mantidos no pmaports por Barnabas Czeman
  (`linux-postmarketos-qcom-sdm660`) e Nickolay Goppen (`alsa-ucm-conf-qcom-sdm660`).
- **Xiaomi**, pelo código GPL do kernel do lavender
  (`techpack/audio/asoc/codecs/max98937.c`, publicado também pelo LineageOS): a tabela de
  inicialização do driver mínimo vem dele.
- **[Magisk](https://github.com/topjohnwu/Magisk)**, de topjohnwu: deu o root usado no
  backup das partições e continua na `boot` do MIUI.
- **[U-Boot](https://u-boot.org)** e **[Phosh](https://phosh.mobi)**.

## Ajuda de IA

O Claude (Anthropic) ajudou na investigação, no driver, nos scripts e na documentação.
O dono do aparelho testou tudo e responde pelo que está aqui. Detalhes no
[README](README.md#uso-de-ia).

Se você é autor de algo usado aqui e quer outro crédito, ou não quer o crédito, abra uma
issue.
