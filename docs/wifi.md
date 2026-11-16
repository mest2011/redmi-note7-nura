# Wi-Fi do Redmi Note 7 no Nura: queda do modem e lentidão

Dois defeitos do driver `ath10k` com o WCN3990 deste aparelho, cada um com um patch pequeno:

| Defeito | Patch |
| --- | --- |
| O modem caía a cada desconexão, e o Wi-Fi não voltava sozinho | [`0001`](../kernel-7.2/0001-ath10k-wcn3990-sem-txbf-apos-vdev-down.patch) |
| Wi-Fi lento (cerca de 20 Mbit/s) em redes WPA3 ou WPA2/WPA3 | [`0002`](../kernel-7.2/0002-ath10k-wcn3990-flag-pmf-no-peer.patch) |

Vale para o kernel `7.2.3` do fork (ver [`kernel-7.2.md`](kernel-7.2.md)). O `7.0.14` do pacote
tem os mesmos defeitos e não recebeu as correções.

| Item | Valor no aparelho testado |
| --- | --- |
| Chip | WCN3990, driver `ath10k_snoc` |
| Firmware | `qmi fw_version 0x101a832b`, de 21/12/2020 (do MIUI `V12.5.1.0.QFGMIXM`) |
| Kernel | `7.2.3-sdm660` |
| Rede | malha WPA2/WPA3 com PMF, 5 GHz no canal 48 (80 MHz) e 2,4 GHz |

O 5 GHz conecta com ou sem os patches, também no `7.0.14`. O que faltava era ele render.

## 1. O modem caía a cada desconexão

### Sintoma

Quando o Wi-Fi perdia o sinal ou trocava de roteador dentro da mesma rede (malha), ele não
voltava sozinho. Só voltava desligando e ligando o Wi-Fi pela interface, ou reiniciando.

No log do kernel, toda desconexão terminava assim:

```
wlan0: deauthenticating from <AP> by local choice (Reason: 3=DEAUTH_LEAVING)
qcom-q6v5-mss 4080000.remoteproc: fatal error received: err_qdi.c:459:EX:wlan_process:1:WLAN RT:4084:PC=b00ca330
remoteproc remoteproc1: crash detected in 4080000.remoteproc: type fatal error
ath10k_snoc 18800000.wifi: firmware crashed!
```

O modem inteiro reinicia. Enquanto ele volta, o NetworkManager tenta religar a interface e
falha (`do-change-link: failure 108`), desiste, e o `wpa_supplicant` fica repetindo
`CTRL-EVENT-SCAN-FAILED ret=-100`. No `7.0.14`, uma troca de roteador chegou a derrubar o modem
4 vezes em 16 s. Desligar e ligar o Wi-Fi reinicia o driver por inteiro, por isso resolvia.

### Causa

Com o debug do driver ligado, a última coisa que o `ath10k` manda antes da queda é sempre a
mesma:

```
ath10k_snoc 18800000.wifi: mac vdev 0 disassoc bssid <AP>
ath10k_snoc 18800000.wifi: wmi tlv vdev down
ath10k_snoc 18800000.wifi: wmi tlv vdev 0 set param 45 value 0x0
```

O parâmetro 45 é o TXBF (beamforming). A função `ath10k_bss_disassoc()` desce o vdev e, em
seguida, zera o TXBF dele. O firmware do WCN3990 deste aparelho não aceita esse comando num
vdev que já desceu: o processo `wlan_process` dá assert, e ele roda dentro do modem.

A pista do TXBF veio de um comentário de SudosuBash na issue
[sdm660-mainline/linux#243](https://github.com/sdm660-mainline/linux/issues/243), que descreve
um sintoma parecido em outros aparelhos SDM630 e SDM660. A issue em si (autenticação que expira
depois de o roteador desassociar o aparelho) continua aberta, e este patch não foi testado
contra ela.

### Correção

[`kernel-7.2/0001-ath10k-wcn3990-sem-txbf-apos-vdev-down.patch`](../kernel-7.2/0001-ath10k-wcn3990-sem-txbf-apos-vdev-down.patch):
em `drivers/net/wireless/ath/ath10k/mac.c`, o `ath10k_bss_disassoc()` deixa de zerar o TXBF
quando o chip é WCN3990 e a interface é estação. O parâmetro volta a ser gravado na
associação seguinte, pelo `ath10k_bss_assoc()`.

Uma série enviada à lista do kernel em outubro de 2026 cita um patch de Fabricio Akio para o
mesmo ponto ("wifi: ath10k: don't reset TxBF on disassociation"). Ele não foi consultado aqui;
se já estiver no kernel que você compila, o `0001` é desnecessário.

### Teste

Kernel `7.2.3-sdm660`, variante Shenchao, em 15/11/2026. "Queda" é uma linha
`fatal error received` no log do kernel.

| Teste | Módulo original | Módulo com o patch |
| --- | --- | --- |
| Desligar e ligar o Wi-Fi (`nmcli radio wifi off` e `on`) | 2 quedas em 2 | 0 quedas em 4; reconecta sozinho |
| Andar pela casa, trocando entre os roteadores da malha (5 GHz e 2,4 GHz) | não repetido no 7.2.3; no `7.0.14`, 4 quedas em 16 s | 4 trocas, cada uma em menos de 1 s, 0 quedas, mesmo IP |
| Uma noite ligado (14 h) | | 0 quedas, 0 desconexões |
| Desligar o aparelho | o modem caiu nos 3 desligamentos conferidos | 1 desligamento, 0 quedas |

O log do debug confirma que, com o patch, o `set param 45` não é mais enviado depois do
`vdev down`.

## 2. Wi-Fi lento em redes com PMF

### Sintoma

O enlace aparece ótimo, mas a transferência não acompanha, e o ping oscila muito:

```
freq: 5240.0
signal: -41 dBm
rx bitrate: 433.3 MBit/s VHT-MCS 9 80MHz short GI VHT-NSS 1
```

| Medida | Valor |
| --- | --- |
| Download | 17 a 24 Mbit/s |
| Upload | 37 a 55 Mbit/s |
| Ping no roteador | média de 37 a 68 ms, picos de 100 a 300 ms |
| Mesma rede, entre dois computadores | 428 / 451 Mbit/s |

Sem perda de pacotes: no download, o servidor retransmitiu 3 segmentos em 19.450.

### Causa

O firmware não agrega quadros. Os contadores dele (`fw_stats` no debugfs do `ath10k`), antes e
depois de uma transferência, mostram uma transmissão por quadro:

| Contador | Diferença |
| --- | --- |
| `MPDU queued` | 37.639 |
| `PPDUs reaped` | 39.584 |

Em Wi-Fi 4 e 5 o normal é juntar dezenas de quadros por transmissão (A-MPDU). Sem isso, um
enlace de 433 Mbit/s fica perto de 45 Mbit/s.

A rede é WPA2/WPA3 e a conexão negocia PMF, a proteção dos quadros de gerência
(`MFP: yes` em `iw dev wlan0 station dump`). O `ath10k` só passa essa informação ao firmware
quando o `firmware-5.bin` anuncia o recurso `mfp`, e o do WCN3990 não anuncia. Sem saber do PMF,
o firmware manda os pedidos de agregação (ADDBA) sem proteção, o roteador os ignora, e nenhum
acordo de agregação é fechado.

Quem achou isso foi Shunsuke Nagashima, na série
["wifi: ath10k: WCN3990 station fixes for PMF and failed connections"](https://lkml.iu.edu/2610.1/19749.html),
medindo num SDM845: 22 Mbit/s numa rede WPA3 e 280 na mesma rede em WPA2. O projeto ROCKNIX
relatou o mesmo em [distribution#3613](https://github.com/ROCKNIX/distribution/pull/3613).

Descartado por medição, neste aparelho: economia de energia do Wi-Fi (desligada, nada mudou),
Bluetooth (bloqueado, nada mudou), calibração (o `board-2.bin` do pacote é idêntico ao
`bdwlan.bin` do MIUI), limitação térmica e CPU.

### Correção

[`kernel-7.2/0002-ath10k-wcn3990-flag-pmf-no-peer.patch`](../kernel-7.2/0002-ath10k-wcn3990-flag-pmf-no-peer.patch):
em `ath10k_peer_assoc_h_crypto()`, a flag de PMF do peer passa a ser enviada também quando o
chip é WCN3990.

É a correção do [patch 1/3](https://lkml.iu.edu/2610.1/19751.html) daquela série, adaptada. O
original cria um campo em `struct ath10k_hw_params`; aqui o teste é por `ar->hw_rev`, para a
`struct ath10k` não mudar de formato e bastar trocar o `ath10k_core.ko` num kernel já
instalado. Para compilar o kernel inteiro, prefira a série original. Os patches 2/3 e 3/3 dela
(conexões que falham) não foram testados aqui.

### Teste

Kernel `7.2.3-sdm660`, em 16/11/2026, 5 GHz, canal 48, 80 MHz, sinal entre -39 e -45 dBm, PMF
ativo. TCP por 8 s em cada sentido, entre o celular e um computador da mesma rede.

| Medida | Só com o `0001` | Com `0001` e `0002` |
| --- | --- | --- |
| Download | 17 a 24 Mbit/s (9 medidas) | 233 a 242 Mbit/s (3 medidas) |
| Upload | 37 a 55 Mbit/s (9 medidas) | 230 a 241 Mbit/s (3 medidas) |
| Ping no roteador, 20 pacotes | média de 37 a 68 ms, máximo de 100 a 300 ms | média de 14 a 15 ms, máximo de 25 a 32 ms |
| Quedas do modem ao desligar e ligar o Wi-Fi | 0 em 5 | 0 em 2 |

O ping foi medido com a economia de energia do Wi-Fi ligada, que é o padrão.

Depois de reiniciar o aparelho, em 16/11/2026, o módulo com os dois patches carregou de
`/lib/modules` no boot e o Wi-Fi associou em 5 GHz 22 s depois de ligar, com PMF e sem queda do
modem. Duas medidas nesse boot: 239 e 240 Mbit/s de download, 216 e 193 de upload, ping com
média de 13 a 14 ms e máximo de 21 a 23 ms.

## Não verificado

Perda total de sinal (sair do alcance de todos os roteadores), o kernel inteiro compilado com
os patches (só o módulo foi compilado), rede só WPA2 sem PMF, a banda de 2,4 GHz depois do
`0002`, outros firmwares do WCN3990 e o kernel `7.0.14`.

Os canais 100 a 144 de 5 GHz aparecem desativados: o rádio se apresenta com o domínio
regulatório da China. Se o seu roteador usar um deles, a rede de 5 GHz não aparece. Isso não foi
tratado aqui.

## Como aplicar

### Compilando o kernel 7.2 inteiro

Siga [`kernel-7.2.md`](kernel-7.2.md) e, antes do `build-nura.sh`, aplique os patches no
checkout do kernel:

```bash
git -C linux apply ../kernel-7.2/0001-ath10k-wcn3990-sem-txbf-apos-vdev-down.patch ../kernel-7.2/0002-ath10k-wcn3990-flag-pmf-no-peer.patch
```

Ajuste o caminho dos patches para onde este repositório estiver. Os dois aplicam sem conflito
na branch `qcom-sdm660-7.2.y`, mas o kernel inteiro com eles não foi compilado nem testado: o
aparelho recebeu só o módulo, como abaixo.

### Só o módulo, com o 7.2.3 já instalado

No PC, no mesmo checkout e com a mesma config do kernel que está no aparelho
(`zcat /proc/config.gz`), em `build-wifi/.config`:

```bash
make -C linux ARCH=arm64 LLVM=1 LOCALVERSION= O=../build-wifi olddefconfig
```

```bash
make -C linux ARCH=arm64 LLVM=1 LOCALVERSION= O=../build-wifi modules_prepare
```

```bash
make -C linux ARCH=arm64 LLVM=1 LOCALVERSION= O=../build-wifi KBUILD_MODPOST_WARN=1 drivers/net/wireless/ath/ath10k/ath10k_core.ko
```

O `KBUILD_MODPOST_WARN=1` é preciso porque não há `vmlinux` nessa pasta. Antes de aplicar os
patches, compile uma vez e compare o `srcversion` com o do aparelho: se forem iguais, o
checkout, a config e o compilador batem.

```bash
modinfo build-wifi/drivers/net/wireless/ath/ath10k/ath10k_core.ko | grep srcversion
```

```bash
ssh <usuário>@172.16.42.1 cat /sys/module/ath10k_core/srcversion
```

Com os patches aplicados e o módulo recompilado, tire os símbolos de debug e comprima:

```bash
llvm-strip --strip-debug -o ath10k_core.ko build-wifi/drivers/net/wireless/ath/ath10k/ath10k_core.ko
```

```bash
zstd -19 -k ath10k_core.ko
```

```bash
scp ath10k_core.ko.zst <usuário>@172.16.42.1:
```

No celular, guarde o original e troque o arquivo:

```bash
sudo cp -p /lib/modules/7.2.3-sdm660/kernel/drivers/net/wireless/ath/ath10k/ath10k_core.ko.zst ~/ath10k_core.ko.zst.original
```

```bash
sudo cp ~/ath10k_core.ko.zst /lib/modules/7.2.3-sdm660/kernel/drivers/net/wireless/ath/ath10k/ath10k_core.ko.zst
```

Recarregue o driver. Faça isso pelo cabo USB, porque o Wi-Fi cai, e num comando só:

```bash
sudo sh -c 'nmcli radio wifi off; sleep 10; rmmod ath10k_snoc ath10k_core; modprobe ath10k_snoc; sleep 6; nmcli radio wifi on'
```

O módulo não é assinado: o kernel carrega e marca `taint`. Reinstalar os módulos do 7.2 (o
`.tar` do [`instalar.sh`](../scripts/kernel-7.2/instalar.sh)) desfaz a troca.

## Como conferir

Módulo carregado (o valor muda a cada compilação; o que importa é ser diferente do original):

```bash
cat /sys/module/ath10k_core/srcversion
```

Quedas do modem neste boot, que devem ficar em 0 depois de desligar e ligar o Wi-Fi:

```bash
journalctl -k -b | grep -c 'fatal error received'
```

Se a conexão usa PMF, que é o caso em que o `0002` faz diferença:

```bash
iw dev wlan0 station dump | grep MFP
```

Para ver se o firmware está agregando, compare `MPDU queued` e `PPDUs reaped` antes e depois de
uma transferência. Sem agregação os dois crescem juntos; com ela, o esperado é o segundo
crescer bem menos. Depois do `0002` só a velocidade foi medida, não esses contadores.

```bash
sudo sh -c "grep -E 'MPDU queued|PPDUs reaped' /sys/kernel/debug/ieee80211/phy*/ath10k/fw_stats"
```

Para ver os comandos que o driver manda ao firmware, ligue o debug (WMI e MAC) e acompanhe o
log. Volte para `0` no fim, porque ele escreve muito durante as buscas de rede:

```bash
echo 0x12 | sudo tee /sys/module/ath10k_core/parameters/debug_mask
```

```bash
journalctl -k -f | grep ath10k
```

`iw dev wlan0 disconnect` não serve para simular a queda: o kernel responde
`Operation not permitted`, porque a conexão pertence ao `wpa_supplicant`.
