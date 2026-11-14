# Kernel 7.2 do sdm660-mainline no Redmi Note 7

O Nura ainda empacota o kernel `7.0.14`. O fork sdm660-mainline já está no `7.2.y` (branch
`qcom-sdm660-7.2.y`), e os 3 patches da GPU já vêm nele. O driver da caixa foi portado para lá e
proposto aos mantenedores:

| O quê | Onde |
| --- | --- |
| Driver MAX98937, binding, árvore do lavender e defconfig | [sdm660-mainline/linux#262](https://github.com/sdm660-mainline/linux/pull/262) |
| Saída `Speaker` no UCM, para o kernel 7.0.14 (`master`) | [sdm660-mainline/alsa-ucm-conf#11](https://github.com/sdm660-mainline/alsa-ucm-conf/pull/11) |
| A mesma saída para o 7.2, sobre o branch `setotau/upstream-sm8250` | branch [`lavender-speaker-lpi`](https://github.com/mest2011/alsa-ucm-conf/tree/lavender-speaker-lpi) |

Este guia é para quem quer testar o 7.2 antes de ele chegar ao Nura. Não há pacote pronto:
você compila o kernel.

## O que muda no 7.2

- **A placa de som** é a do `sm8250.c` e se apresenta com o driver `sdm660`. O UCM do sistema só
  conhece `sdm660-internal`, então o PulseAudio cai no perfil genérico `stereo-fallback`.
- **As portas internas** mudaram de nome: `INT0_MI2S_RX` virou `LPI_MI2S_RX_0`, e `INT3_MI2S_TX`
  virou `LPI_MI2S_TX_3`. O branch `setotau/upstream-sm8250` do `alsa-ucm-conf`, do mantenedor,
  já usa os nomes novos e tem `conf.d/sdm660`.
- **O formato I2S do amplificador** já é informado pelo `sm8250.c`. O trecho do
  `sdm660-internal.c` do patch do 7.0.14 não é mais necessário.

## Testado (14/11/2026)

Aparelho Shenchao, 4 GB, kernel `7.2.3-sdm660` deste procedimento, Nura edge, Phosh e
PulseAudio:

| Teste | Resultado |
| --- | --- |
| Boot pelo U-Boot | Nura no ar em 30 s, rede USB e Wi-Fi funcionando |
| Driver da caixa | `snd_soc_max98937` carregado e em uso; placa `sdm660 - Xiaomi Redmi Note 7` |
| Caixa, só pela rota `PRI_MI2S_RX` | tom de 500 Hz de -64/-78 dB (ruído) para -56/-57 dB, 4 de 4; com a rota desligada, fica no ruído |
| UCM do 7.2 pelo PulseAudio | perfil `HiFi (Mic, Speaker)`, caixa como saída padrão |
| Caixa → chamada → caixa | -43 / -72 / -43 dB, também com o som já tocando |
| GPU | 0 erros em 16 min de boot, com 10 min de Chromium abrindo e fechando |
| UCM do 7.2 depois de reiniciar | o PulseAudio sobe sozinho com ele, no perfil `HiFi (Mic, Speaker)` |
| Partições do MIUI | `boot` e `recovery` com hash igual antes e depois |

**GPU com o Brave:** no segundo boot apareceram 2 `gpu fault` aos 199 s, com o Brave apontado como
`offending task`. O kernel recuperou a GPU (`hangcheck recover`), e a interface continuou
respondendo, sem processo preso. Não é o freeze corrigido pelos patches, que travava a tela. A
causa não foi investigada, e não sei se acontece também no 7.0.14.

Medições com o microfone de um notebook ao lado do celular, comparando a faixa de 500 Hz. São
comparativas.

**Não testado no 7.2:** uso por horas, fone P2, microfone, bateria e suspensão.

## Como compilar

Num PC com Linux, com `clang`, `lld` e as dependências normais de compilar kernel:

```bash
git clone --depth 30 --branch lavender-max98937 https://github.com/mest2011/linux.git
```

Copie do Nura 7.0.14 a config e o initramfs atuais para uma pasta de trabalho:

```bash
mkdir teste72
```

```bash
ssh <usuário>@172.16.42.1 'zcat /proc/config.gz' > teste72/config-7.0.14-nura
```

```bash
ssh <usuário>@172.16.42.1 'cat /boot/initramfs' > teste72/initramfs-7.0.14
```

Compile. O script parte da config do Nura e soma o que o `sdm660_defconfig` do 7.2 liga, como
o `SND_SOC_SM8250`:

```bash
KSRC=$PWD/linux T=$PWD/teste72 ./scripts/kernel-7.2/build-nura.sh
```

Monte o initramfs do 7.2. Ele é o do 7.0.14 com os mesmos módulos (GPU, painel, toque e carga)
trocados pelos do 7.2:

```bash
T=$PWD/teste72 ./scripts/kernel-7.2/initramfs72.sh
```

Empacote os módulos e gere os hashes:

```bash
tar -C teste72/stage/lib/modules -cf teste72/modules-7.2.3-sdm660.tar 7.2.3-sdm660
```

```bash
cd teste72 && sha256sum vmlinuz-7.2 initramfs-7.2 sdm660-xiaomi-lavender-shenchao-7.2.dtb modules-7.2.3-sdm660.tar > SHA256SUMS && cd ..
```

O `.dtb` gerado é o da Shenchao. Para Tianma ou BOE, troque o nome no `build-nura.sh` e no
`instalar.sh`.

## Como instalar ao lado do 7.0.14

O instalador **não usa `apk` nem `boot-deploy`**: copia o kernel, o initramfs e o `.dtb` para o
`/boot` com nomes próprios e os módulos para `/lib/modules/7.2.3-sdm660`. Depois põe uma entrada
`teste72` como padrão no `extlinux.conf`, mantendo a do 7.0.14, e salva o arquivo original em
`extlinux.conf.antes-7.2`. Ele para se a proteção do `/etc/deviceinfo` não estiver lá, e
compara o hash das partições do MIUI antes e depois.

```bash
scp teste72/vmlinuz-7.2 teste72/initramfs-7.2 teste72/*.dtb teste72/modules-7.2.3-sdm660.tar teste72/SHA256SUMS scripts/kernel-7.2/instalar.sh scripts/kernel-7.2/voltar.sh <usuário>@172.16.42.1:teste72/
```

```bash
ssh -t <usuário>@172.16.42.1 sudo sh teste72/instalar.sh
```

Ele reinicia no fim, e o celular cai no MIUI. Volte com `adb reboot recovery`: o U-Boot sobe o 7.2.

**Se o 7.2 não ligar:** segure o Power até reiniciar (liga no MIUI) e restaure o menu pelo root:

```bash
adb shell su -c 'mkdir -p /data/local/tmp/sd && mount -t ext2 /dev/block/mmcblk1p1 /data/local/tmp/sd && cp /data/local/tmp/sd/extlinux/extlinux.conf.antes-7.2 /data/local/tmp/sd/extlinux/extlinux.conf && sync && umount /data/local/tmp/sd'
```

**Para voltar ao 7.0.14 com o 7.2 ligando:**

```bash
sudo sh teste72/voltar.sh
```

## UCM do 7.2 sem root

Sem um UCM que conheça o 7.2, a caixa até toca (a rota fica salva pelo `alsactl`), mas o seletor de
saída do Phosh não troca entre caixa e chamada. Dá para usar o UCM do 7.2 só no seu usuário, sem
mexer no sistema e sem ser desfeito por `apk upgrade`:

```bash
git clone --branch lavender-speaker-lpi https://github.com/mest2011/alsa-ucm-conf.git ucm-7.2
```

```bash
mkdir -p ~/.local/share && cp -r ucm-7.2/ucm2 ~/.local/share/ucm2-lavender-7.2
```

```bash
mkdir -p ~/.config/environment.d && echo "ALSA_CONFIG_UCM2=$HOME/.local/share/ucm2-lavender-7.2" > ~/.config/environment.d/50-ucm-lavender-7.2.conf
```

Reinicie. Para conferir:

```bash
pactl list cards | grep 'Active Profile'
```

O esperado é `HiFi (Mic, Speaker)`. Para voltar ao UCM do sistema, apague o arquivo em
`~/.config/environment.d/` e reinicie.

Testado no aparelho: depois de reiniciar, o PulseAudio subiu com essa pasta, no perfil
`HiFi (Mic, Speaker)`, com a caixa como saída padrão e o serviço `redmi-audio-reabrir` ativo.
