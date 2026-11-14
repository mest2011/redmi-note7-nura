# Redmi Note 7 (lavender) com Nura

Patches, scripts e um tutorial completo para usar o Nura (ex-postmarketOS) no Redmi Note 7
(lavender, Snapdragon 660) em dual boot com o MIUI. O MIUI continua ligando normal; o Nura
sobe de um cartão SD quando você pede. Este repositório também corrige duas coisas que
faltavam: a caixa de som principal, que ficava muda, e a interface, que congelava.

Projeto pessoal. Não tem ligação oficial com o Nura, o sdm660-mainline nem a Xiaomi.

> **English summary.** Patches and a step-by-step guide to run Nura (formerly postmarketOS)
> on the Xiaomi Redmi Note 7 (lavender, SDM660), dual-booting with MIUI through U-Boot in the
> `recovery` partition. Adds a minimal MAX98937 speaker amp driver plus the lavender DT and
> UCM bits (the stock `max98927` driver probes but stays silent), and carries three
> `FROMLIST` Adreno 5xx patches by Fabricio Akio that fix GPU hangs. Built with AI
> assistance (Claude) and tested on one device. See [CREDITOS.md](CREDITOS.md).

## Estado (novembro de 2026)

| Item | Estado |
| --- | --- |
| Dual boot | MIUI liga normal; `adb reboot recovery` abre o U-Boot, que sobe o Nura do cartão SD |
| Caixa principal (MAX98937) | toca e é a saída padrão, com o driver deste repositório |
| Freeze da GPU (Adreno 512) | corrigido com 3 patches do fork: 30 min de carga sem erro |
| Wi-Fi | funciona, só em 2,4 GHz |
| Docker nativo | roda com overlayfs e cgroup v2 |
| Sem suporte no Nura | dados móveis, chamadas, câmera, GPS e OTG |

Testado num aparelho só: variante Shenchao (painel NT36672A), 4 GB, MIUI 12.5.1
(`V12.5.1.0.QFGMIXM`) com Magisk 31.1, U-Boot `v2026.10-sdm660`, Nura edge com Phosh,
kernel `7.0.14-sdm660`. O kernel `7.2.3` do fork também foi testado, com o driver da caixa:
ver [`docs/kernel-7.2.md`](docs/kernel-7.2.md).

O driver da caixa foi proposto ao sdm660-mainline em
[linux#262](https://github.com/sdm660-mainline/linux/pull/262) e
[alsa-ucm-conf#11](https://github.com/sdm660-mainline/alsa-ucm-conf/pull/11).

---

## Tutorial de instalação

Leia tudo antes de começar. Leva uma tarde, quase toda esperando backup e compilação.

### Antes de começar: riscos

- **Desbloquear o bootloader apaga o celular.** Faça backup das suas fotos e arquivos antes.
- Este tutorial grava só três partições: `recovery` (U-Boot), `dtbo` (apagada) e, se você
  quiser root fixo, `boot` (MIUI com Magisk). Nada antes da `boot` é tocado, e o fastboot da
  Xiaomi continua sendo o caminho de resgate.
- **Nunca** use `fastboot oem lock`, `flash_all_lock` nem grave `xbl`, `abl`, `tz`, `rpm`,
  `hyp` ou as cópias `*bak`. Isso sim pode inutilizar o aparelho.
- Não aceite atualização (OTA) do MIUI enquanto o dual boot existir.
- Seu backup de partições vai conter IMEI, MAC e número de série. Guarde fora da nuvem e nunca
  publique.

### O que você precisa

| Item | Para quê |
| --- | --- |
| Redmi Note 7 (lavender) com MIUI | o aparelho |
| Cartão microSD de 16 GB ou mais | onde o Nura fica instalado |
| PC com Linux (ou VM, ou WSL2) | rodar o `pmbootstrap`, que gera a imagem do Nura |
| Cabo USB de dados | `adb` e `fastboot` |
| `adb` e `fastboot` no PC | pacote `android-tools` ou `android-sdk-platform-tools` |
| ROM oficial do MIUI da **mesma versão** do seu celular | tirar a `boot.img` para o Magisk |
| Uns 20 GB livres no PC | backup das partições e compilação |

### Etapa 1: desbloquear o bootloader

Se o seu já está desbloqueado, pule para a Etapa 2. No fastboot (desligue, segure
`Power + Vol−`), confira:

```bash
fastboot getvar unlocked
```

`unlocked: yes` quer dizer desbloqueado. Se vier `no`, use o **Mi Unlock** oficial
da Xiaomi (Windows, conta Mi vinculada ao aparelho em *Opções do desenvolvedor → Status do Mi
Unlock*, com espera de alguns dias). O aparelho testado aqui já veio desbloqueado; esta etapa
não foi refeita para este tutorial.

### Etapa 2: descobrir a variante da tela

O lavender tem três telas: **Shenchao**, **Tianma** e **BOE**, e o Nura precisa saber qual é a
sua. Com o celular no MIUI, a depuração USB ligada e root (Etapa 3), rode:

```bash
adb shell su -c 'cat /proc/cmdline' | tr ' ' '\n' | grep mdss_mdp.panel
```

O valor tem `shenchao`, `tianma` ou `boe` no nome. Anote. Se ainda não tem root, deixe para
depois da Etapa 3.

### Etapa 3: root temporário com o Magisk

Root serve para fazer o backup sem TWRP. Os TWRP oficiais (3.5.2, 3.6.2 e 3.7.0) reiniciam no
`fastboot boot` deste firmware, então o caminho é o Magisk.

1. Baixe a ROM **fastboot** oficial da mesma versão do seu MIUI (veja em *Configurações → Sobre
   o telefone*) e confira o MD5 publicado.
2. Tire a `boot.img` do arquivo da ROM (pasta `images/`).
3. Instale o app do Magisk no MIUI, copie a `boot.img` para o celular e use *Instalar → Corrigir
   um arquivo*. Ele gera `magisk_patched-....img` em `Download/`.
4. Traga a imagem para o PC:

```bash
adb pull /sdcard/Download/magisk_patched-XXXXX.img .
```

5. Reinicie no fastboot (`adb reboot bootloader`) e inicie a imagem **só na RAM**, sem gravar:

```bash
fastboot boot magisk_patched-XXXXX.img
```

6. No app do Magisk, aba **SuperUsuário**, adicione o `Shell` à mão (botão `+`). Na versão 31.1,
   sem isso o `su` é negado na hora, sem aparecer pedido na tela.
7. Teste:

```bash
adb shell su -c id
```

A saída tem que começar com `uid=0(root)`.

**Root fixo (recomendado):** no aparelho testado, a `boot` ficou com o Magisk gravado
(`fastboot flash boot magisk_patched-XXXXX.img`). O MIUI tem um `install-recovery.sh` que poderia
regravar a `recovery` original e apagar o U-Boot. Com a `boot` modificada, isso não aconteceu
em nenhum boot. A explicação provável, não confirmada, é que o patch dele falha. Sem Magisk na
`boot`, esse comportamento não foi testado.

### Etapa 4: backup de todas as partições

Com o root funcionando, copie cada partição, menos a `userdata`, para o PC:

```bash
mkdir -p backup-lavender && cd backup-lavender
```

```bash
for p in $(adb shell su -c 'ls /dev/block/bootdevice/by-name' | tr -d '\r'); do [ "$p" = userdata ] && continue; adb shell su -c "dd if=/dev/block/bootdevice/by-name/$p of=/sdcard/bk.img" && adb pull /sdcard/bk.img "$p.img" && adb shell rm /sdcard/bk.img; done
```

```bash
sha256sum *.img > SHA256SUMS
```

Guarde essa pasta em dois lugares. As que importam para voltar atrás são `boot.img`,
`recovery.img` e `dtbo.img`.

### Etapa 5: gerar a imagem do Nura

No PC com Linux:

```bash
git clone https://gitlab.nura.eco/nura/pmbootstrap.git
```

```bash
python3 pmbootstrap/pmbootstrap.py init
```

Responda assim:

| Pergunta | Resposta |
| --- | --- |
| Channel | `edge` |
| Vendor / Device | `xiaomi` / `lavender` |
| Kernel | a variante da Etapa 2 (`shenchao`, `tianma` ou `boe`) |
| User interface | `phosh` (usada aqui) |
| Username | o usuário que você quiser |

A versão usada aqui foi o `main` do pmbootstrap de 02/11/2026. A 3.12.1 ainda esperava o
endereço antigo (`gitlab.postmarketos.org`) no clone do pmaports; se der erro de remoto, use o
`main`.

Com um leitor de cartão no PC, grave direto no cartão (troque `sdX` pelo cartão, confira com
`lsblk`: **o dispositivo errado apaga o disco do PC**):

```bash
python3 pmbootstrap/pmbootstrap.py install --sdcard=/dev/sdX
```

**Caminho testado aqui, sem leitor de cartão:** gerar a imagem e gravar pelo próprio celular,
com root.

```bash
python3 pmbootstrap/pmbootstrap.py install --no-sparse
```

```bash
python3 pmbootstrap/pmbootstrap.py export
```

O `export` mostra onde ficou o `xiaomi-lavender.img`. Com o cartão no celular e o MIUI ligado:

```bash
adb push xiaomi-lavender.img /sdcard/
```

```bash
adb shell su -c 'dd if=/sdcard/xiaomi-lavender.img of=/dev/block/mmcblk1 bs=4M && sync'
```

No MIUI, o cartão é `/dev/block/mmcblk1`. Confira antes com
`adb shell su -c 'ls -la /dev/block/mmcblk1*'`: ele precisa ter o tamanho do cartão.

### Etapa 6: U-Boot na partição `recovery`

O U-Boot do sdm660-mainline é o "GRUB" que sobe o Nura do cartão.

1. Baixe `boot-uboot-sdm660-xiaomi-lavender.img` da
   [release v2026.10-sdm660](https://github.com/sdm660-mainline/u-boot/releases/tag/v2026.10-sdm660).
2. No fastboot, apague a `dtbo`. **Com a `dtbo` original o U-Boot não sobe**: o ABL responde
   `Booting OKAY` e volta ao fastboot, sem erro. Sem ela, o MIUI continua ligando com toque,
   Wi-Fi, áudio, sensores e câmeras.

```bash
fastboot erase dtbo
```

3. Teste o U-Boot só na RAM. Tem que aparecer o logo e o menu do U-Boot, e o Nura deve começar
   a subir do cartão:

```bash
fastboot boot boot-uboot-sdm660-xiaomi-lavender.img
```

4. Funcionou? Volte ao fastboot e grave na `recovery`:

```bash
fastboot flash recovery boot-uboot-sdm660-xiaomi-lavender.img
```

O U-Boot vai na `recovery`, não na `boot`, porque o menu dele não tem entrada para o Android.
Assim o MIUI continua na `boot`.

### Etapa 7: primeiro boot do Nura

1. Ligue normal. O MIUI deve abrir.
2. Vá para o Nura:

```bash
adb reboot recovery
```

`Power + Vol+` ao ligar deve fazer o mesmo, mas não foi testado. O Nura leva cerca de 100 s.
3. Pelo cabo USB, o Nura cria uma rede própria e já vem com SSH:

```bash
ssh <seu-usuário>@172.16.42.1
```

4. **Expanda a raiz para o cartão todo.** No aparelho testado ela não expandiu sozinha. Veja com
   `df -h /`: se o tamanho for bem menor que o cartão, expanda. No Nura, o cartão é `/dev/mmcblk2`
   (confira com `lsblk`). Primeiro mova a tabela GPT de reserva para o fim do cartão:

```bash
sudo sfdisk --relocate gpt-bak-std /dev/mmcblk2
```

   Depois estique a partição 2 (a raiz) até o fim:

```bash
echo ', +' | sudo sfdisk -N 2 --no-reread /dev/mmcblk2
```

   Reinicie (vai cair no MIUI; volte com `adb reboot recovery`) e estique o sistema de arquivos:

```bash
sudo resize2fs /dev/mmcblk2p2
```

   No aparelho testado foram estes comandos, com o sistema no ar. A ordem exata e o
   `--no-reread` foram reconstruídos do registro: leia a saída de cada um antes do próximo.

### Etapa 8: proteger o MIUI (obrigatório)

Em dual boot, **instalar ou atualizar o kernel no Nura grava na partição `boot` do MIUI**, e o MIUI
para de ligar. Isso aconteceu no aparelho testado. A causa é
`deviceinfo_flash_kernel_on_update="true"` no `deviceinfo` do lavender. Antes de qualquer
`apk add`, `apk upgrade` ou `mkinitfs`:

```bash
echo 'deviceinfo_flash_kernel_on_update="false"' | sudo tee /etc/deviceinfo
```

Confira:

```bash
cat /etc/deviceinfo
```

### Etapa 9: instalar a caixa de som e a correção da GPU

No Nura, baixe os pacotes da [release](../../releases/latest):

```bash
wget https://github.com/mest2011/redmi-note7-nura/releases/download/v2026.11.05/linux-postmarketos-qcom-sdm660-7.0.14-r5.apk
```

```bash
wget https://github.com/mest2011/redmi-note7-nura/releases/download/v2026.11.05/alsa-ucm-conf-qcom-sdm660-1.2.15_git20260721-r3.apk
```

```bash
wget https://github.com/mest2011/redmi-note7-nura/releases/download/v2026.11.05/SHA256SUMS
```

```bash
sha256sum -c SHA256SUMS
```

Com a proteção da Etapa 8 no lugar, instale:

```bash
sudo apk add --allow-untrusted linux-postmarketos-qcom-sdm660-7.0.14-r5.apk alsa-ucm-conf-qcom-sdm660-1.2.15_git20260721-r3.apk
```

Os pacotes não são assinados, por isso o `--allow-untrusted`. O kernel traz o driver da caixa e os
patches da GPU para as três variantes de tela, mas só a Shenchao foi testada.

Depois, o serviço que reabre a saída de som quando você troca entre caixa e chamada:

```bash
git clone https://github.com/mest2011/redmi-note7-nura.git
```

```bash
sudo install -m 755 redmi-note7-nura/scripts/redmi-audio-reabrir /usr/local/bin/redmi-audio-reabrir
```

```bash
sudo install -m 644 redmi-note7-nura/scripts/redmi-audio-reabrir.service /usr/lib/systemd/user/redmi-audio-reabrir.service
```

```bash
systemctl --user enable --now redmi-audio-reabrir.service
```

Reinicie o Nura. Ele cai no MIUI; volte com `adb reboot recovery`.

### Etapa 10: conferir

| Teste | Comando no Nura | Esperado |
| --- | --- | --- |
| Kernel novo | `uname -r` | `7.0.14-sdm660` e `apk info -v linux-postmarketos-qcom-sdm660` em `r5` |
| Amplificador | `sudo dmesg \| grep -i max98937` | a linha `MAX98937 revisao 0x43`, sem erro |
| Perfil de som | `pactl list cards \| grep 'Active Profile'` | um perfil `HiFi` com `Speaker` |
| Som | `speaker-test -D pulse -c 2 -t sine -f 500 -l 1` | tom saindo pela caixa de baixo |
| GPU | `sudo journalctl -k \| grep -c -E 'hangcheck\|preemption timed out'` | `0` |
| MIUI intacto | reinicie e veja o MIUI abrir | MIUI com Magisk |

O volume da caixa começa baixo de propósito: sem a proteção DSM do Android, o driver usa o ganho
seguro da Xiaomi. Para subir um pouco, como no aparelho testado:

```bash
amixer -c0 cset name='Speaker Volume' 2
```

```bash
amixer -c0 cset name='Digital Volume' 48
```

```bash
sudo alsactl store
```

O máximo é `5` e `56`, os valores do MIUI. Sem DSM, suba aos poucos.

---

## No dia a dia

- **Ir para o Nura:** `adb reboot recovery` no MIUI.
- **Voltar ao MIUI:** reiniciar o Nura. Depois de uma queda de energia o aparelho liga no MIUI.
- **Wi-Fi:** só redes de 2,4 GHz. Desconectar pode derrubar o modem até reiniciar.
- **Apps sumidos no Phosh:** o filtro adaptativo esconde apps sem `X-Purism-FormFactor`. Copie o
  `.desktop` para `~/.local/share/applications/` e acrescente
  `X-Purism-FormFactor=Workstation;Mobile;`.
- **Processos em segundo plano pelo SSH:** `nohup` e `setsid` morrem ao fechar o `ssh`. Use
  `systemd-run --user`.
- **Cabo USB sem IPv4 depois de reconectar:** use IPv6 de enlace, `ping6 ff02::1%<interface>` e
  `ssh <usuário>@<fe80::...>%<interface>`.

## Atualizações

Antes de `apk upgrade`, simule:

```bash
sudo apk upgrade -s
```

Se aparecer `linux-postmarketos-qcom-sdm660` ou `alsa-ucm-conf-qcom-sdm660`, o pacote do
repositório do Nura vai trocar o deste projeto e tirar o driver da caixa e a correção da GPU. Nesse
caso, recompile com os patches sobre a versão nova (ver [Compilando](#compilando-você-mesmo)) ou
espere uma release nova aqui. A proteção da Etapa 8 precisa continuar em `/etc/deviceinfo`.

## Problemas comuns

| Sintoma | Causa e saída |
| --- | --- |
| `fastboot boot` do U-Boot responde `OKAY` e volta ao fastboot | a `dtbo` não foi apagada (Etapa 6) |
| MIUI não liga depois de instalar um kernel no Nura | o kernel foi gravado na `boot`. No fastboot, regrave a `boot` do backup (a com Magisk) e crie a proteção da Etapa 8 |
| Nura não liga depois de mexer no `/boot` | ligue no MIUI e corrija o cartão com root (abaixo) |
| Sem som na caixa | confira `amixer -c0 cget name='PRI_MI2S_RX Audio Mixer MultiMedia1'` com a caixa ativa e reinicie o PulseAudio com `pulseaudio -k` (o servidor é o PulseAudio, não o PipeWire) |
| Caixa muda depois de trocar de saída com algo tocando | o serviço `redmi-audio-reabrir` não está ativo (Etapa 9) |
| `su` negado sem pedido na tela | adicione o `Shell` na aba SuperUsuário do Magisk |

**Corrigir o cartão pelo MIUI, sem o Nura ligar:**

```bash
adb shell su -c 'mkdir -p /data/local/tmp/sd && mount -t ext2 /dev/block/mmcblk1p1 /data/local/tmp/sd && ls /data/local/tmp/sd/extlinux'
```

O `extlinux/extlinux.conf` ali é o menu do U-Boot. Depois de corrigir, desmonte com
`adb shell su -c 'umount /data/local/tmp/sd'`.

## Voltar ao MIUI puro

No fastboot, com as imagens do seu backup (Etapa 4):

```bash
fastboot flash boot boot.img
```

```bash
fastboot flash recovery recovery.img
```

```bash
fastboot flash dtbo dtbo.img
```

Esse caminho não foi executado no aparelho testado.

---

## Compilando você mesmo

Num checkout do pmaports do Nura, no commit `31482d7d5233` ou próximo:

```bash
./aplicar-no-pmaports.sh <caminho-do-pmaports>
```

```bash
python3 pmbootstrap/pmbootstrap.py build --force --arch aarch64 linux-postmarketos-qcom-sdm660 alsa-ucm-conf-qcom-sdm660
```

O script copia os patches, aplica as mudanças dos `APKBUILD` e confere os hashes. O kernel levou
33 min na primeira compilação, num PC de 12 núcleos.

## O que tem aqui

| Pasta | Conteúdo |
| --- | --- |
| [`docs/dual-boot.md`](docs/dual-boot.md) | Detalhes do dual boot, o incidente da `boot`, riscos e medições |
| [`docs/audio.md`](docs/audio.md) | Caixa principal: o chip, o driver, o UCM e o serviço de troca de saída |
| [`docs/gpu.md`](docs/gpu.md) | Freeze da GPU: sintoma, patches e teste |
| [`docs/kernel-7.2.md`](docs/kernel-7.2.md) | Kernel 7.2 do fork: o que muda, testes, como compilar e instalar ao lado do 7.0.14 |
| [`kernel/`](kernel/) | `0001` driver da caixa e árvore do lavender; `0002` a `0004` patches da GPU |
| [`ucm/`](ucm/) | Saída `Speaker` no `alsa-ucm-conf` do lavender |
| [`pmaports/`](pmaports/) | Mudanças nos `APKBUILD` e na config do kernel do pmaports |
| [`scripts/`](scripts/) | Serviço `redmi-audio-reabrir`, `/etc/deviceinfo` de proteção, teste de carga da GPU e, em `kernel-7.2/`, compilar e instalar o 7.2 |
| [`aplicar-no-pmaports.sh`](aplicar-no-pmaports.sh) | Copia os patches para um checkout do pmaports e confere os hashes |

## Uso de IA

A investigação, o driver, a adaptação dos patches e esta documentação foram feitos com ajuda do
Claude (Anthropic). Tudo foi testado no aparelho pelo dono, que responde pelo que está aqui.

O Nura proíbe contribuições feitas, total ou parcialmente, com IA generativa
([política](https://docs.nura.eco/policies-and-processes/development/ai-policy.html)). Por isso
nada daqui foi enviado ao Nura. Respeite essa regra: não mande estes patches para lá. O driver da
caixa foi proposto ao sdm660-mainline, que aceita contribuição com IA declarada.

## Créditos e licenças

Os autores de cada parte estão em [CREDITOS.md](CREDITOS.md). Cada arquivo segue a licença do
projeto de onde veio:

| Arquivos | Licença |
| --- | --- |
| `kernel/*.patch` | GPL-2.0-only, como o Linux |
| `ucm/*.patch` | BSD-3-Clause, como o `alsa-ucm-conf` |
| `pmaports/*.diff` | GPL-3.0, como o pmaports |
| Scripts e documentação | MIT, ver [LICENSE](LICENSE) |
