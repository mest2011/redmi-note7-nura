# Créditos

Este repositório junta trabalho de muita gente. O que é deste repositório é pouco: o
driver mínimo do MAX98937, as ligações na árvore do lavender, a saída `Speaker` do UCM,
o serviço de troca de saída e a documentação. O resto vem dos projetos abaixo.

## Patches de terceiros incluídos

| Arquivo | Autor | Origem |
| --- | --- | --- |
| `kernel/0002-a5xx-reset-ao-retomar.patch` | Fabricio Akio | [`sdm660-mainline/linux@be8062b9b02a`](https://github.com/sdm660-mainline/linux/commit/be8062b9b02a) |
| `kernel/0003-a5xx-latencia-cpu.patch` | Fabricio Akio | [`sdm660-mainline/linux@b63149ee8311`](https://github.com/sdm660-mainline/linux/commit/b63149ee8311) |
| `kernel/0004-a5xx-wptr-sob-trava.patch` | Fabricio Akio | [`sdm660-mainline/linux@45b54a7c4c87`](https://github.com/sdm660-mainline/linux/commit/45b54a7c4c87), enviado à [lista do kernel](https://lore.kernel.org/r/20261031-a5xx-wptr-lock-v1-1-fa7d7b9a7fbe@gmail.com) |

Os três estão como no fork, sem alteração no conteúdo, com o `Signed-off-by` original.
São eles que corrigem o freeze da GPU. O nome do arquivo foi traduzido; o assunto do
commit não.

## Base de que este trabalho depende

- **[sdm660-mainline](https://github.com/sdm660-mainline):** o kernel mainline do SDM660
  (tag `v7.0.14-sdm660`), o U-Boot que sobe o Nura pela `recovery` (`v2026.10-sdm660`) e o
  `alsa-ucm-conf` do SDM660. Obrigado aos mantenedores e contribuidores.
- **Nickolay Goppen**, pelo branch `upstream-sm8250` do `alsa-ucm-conf` do sdm660-mainline, que
  adapta o UCM aos nomes do kernel 7.2. A saída `Speaker` do 7.2 foi escrita sobre ele.
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
