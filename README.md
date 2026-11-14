# Redmi Note 7 (lavender) com Nura

Patches, scripts e documentação para usar o Nura (ex-postmarketOS) no Redmi Note 7
(lavender, Snapdragon 660) em dual boot com o MIUI. Este repositório corrige duas coisas
que faltavam: a caixa de som principal, que ficava muda, e a interface, que congelava.

Projeto pessoal. Não tem ligação oficial com o Nura, o sdm660-mainline nem a Xiaomi.

> **English summary.** Patches and notes to run Nura (formerly postmarketOS) on the
> Xiaomi Redmi Note 7 (lavender, SDM660), dual-booting with MIUI through U-Boot in the
> `recovery` partition. Adds a minimal MAX98937 speaker amp driver plus the lavender DT
> and UCM bits (the stock `max98927` driver probes but stays silent), and carries three
> `FROMLIST` Adreno 5xx patches by Fabricio Akio that fix GPU hangs. Built with AI
> assistance (Claude) and tested on one device. See [CREDITOS.md](CREDITOS.md).

## Estado (05/11/2026)

| Item | Estado |
| --- | --- |
| Dual boot | MIUI liga normal; `adb reboot recovery` abre o U-Boot, que sobe o Nura do cartão SD |
| Caixa principal (MAX98937) | toca e é a saída padrão, com o driver mínimo deste repo |
| Freeze da GPU (Adreno 512) | corrigido com 3 patches do fork: 30 min de carga sem erro, falta uso por horas |
| Wi-Fi | funciona, só em 2,4 GHz |
| Docker nativo | `hello-world` roda com overlayfs e cgroup v2 |
| Sem suporte no Nura | dados móveis, chamadas, câmera, GPS e OTG |

Testado num aparelho só: variante Shenchao (painel NT36672A), 4 GB, MIUI 12.5.1 com Magisk
31.1, U-Boot `v2026.10-sdm660`, Nura edge com Phosh, kernel `7.0.14-sdm660`, pmaports
`31482d7d5233`.

## O que tem aqui

| Pasta | Conteúdo |
| --- | --- |
| [`docs/dual-boot.md`](docs/dual-boot.md) | Como o dual boot foi montado, como alternar, como voltar ao MIUI, riscos |
| [`docs/audio.md`](docs/audio.md) | Caixa principal: o chip, o driver, o UCM e o serviço de troca de saída |
| [`docs/gpu.md`](docs/gpu.md) | Freeze da GPU: sintoma, patches e teste |
| [`kernel/`](kernel/) | `0001` driver da caixa e árvore do lavender; `0002` a `0004` patches da GPU |
| [`ucm/`](ucm/) | Saída `Speaker` no `alsa-ucm-conf` do lavender |
| [`pmaports/`](pmaports/) | Mudanças nos `APKBUILD` e na config do kernel do pmaports |
| [`scripts/`](scripts/) | Serviço `redmi-audio-reabrir`, `/etc/deviceinfo` de proteção e teste de carga da GPU |
| [`aplicar-no-pmaports.sh`](aplicar-no-pmaports.sh) | Copia os patches para um checkout do pmaports e confere os hashes |

## Antes de instalar qualquer kernel no Nura

Em dual boot, **instalar ou atualizar o kernel grava na partição `boot` do MIUI**, e o MIUI
deixa de ligar. O `deviceinfo` do lavender traz `deviceinfo_flash_kernel_on_update="true"`.
Crie a proteção antes de qualquer `apk add`, `apk upgrade` ou `mkinitfs`:

```bash
sudo install -m 644 scripts/etc/deviceinfo /etc/deviceinfo
```

Os detalhes estão em [`docs/dual-boot.md`](docs/dual-boot.md#incidente-o-kernel-gravou-na-boot-do-miui).

## Como usar

**Pacotes prontos:** a [release](../../releases) traz o kernel `7.0.14-r5` e o UCM `r3`
compilados, sem assinatura. No celular, depois da proteção acima:

```bash
sudo apk add --allow-untrusted linux-postmarketos-qcom-sdm660-7.0.14-r5.apk alsa-ucm-conf-qcom-sdm660-1.2.15_git20260721-r3.apk
```

**Compilando:** num checkout do pmaports do Nura, no commit `31482d7d5233` ou próximo:

```bash
./aplicar-no-pmaports.sh <caminho-do-pmaports>
```

```bash
pmbootstrap build --force --arch aarch64 linux-postmarketos-qcom-sdm660 alsa-ucm-conf-qcom-sdm660
```

Depois instale o serviço de áudio, como em [`docs/audio.md`](docs/audio.md#serviço-da-troca-de-saída).

**Atenção:** um kernel mais novo do repositório do Nura substitui este e tira o driver da
caixa e os patches da GPU. Reaplique os patches ao atualizar.

## Uso de IA

A investigação, o driver, a adaptação dos patches e esta documentação foram feitos com
ajuda do Claude (Anthropic), num computador do dono do aparelho. Tudo foi testado no
aparelho, mas o driver não passou por revisão de um mantenedor do kernel.

O Nura proíbe contribuições feitas, total ou parcialmente, com IA generativa
([política](https://docs.nura.eco/policies-and-processes/development/ai-policy.html)).
Por isso nada daqui foi enviado ao Nura. Respeite essa regra: não mande estes patches para
lá.

## Créditos e licenças

Os autores de cada parte estão em [CREDITOS.md](CREDITOS.md). Cada arquivo segue a
licença do projeto de onde veio:

| Arquivos | Licença |
| --- | --- |
| `kernel/*.patch` | GPL-2.0-only, como o Linux |
| `ucm/*.patch` | BSD-3-Clause, como o `alsa-ucm-conf` |
| `pmaports/*.diff` | GPL-3.0, como o pmaports |
| Scripts e documentação | MIT, ver [LICENSE](LICENSE) |
