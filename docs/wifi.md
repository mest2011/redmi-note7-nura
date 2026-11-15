# Wi-Fi do Redmi Note 7 no Nura: o modem caía a cada desconexão

Vale para o kernel `7.2.3` do fork (ver [`kernel-7.2.md`](kernel-7.2.md)). O `7.0.14` do pacote
tem o mesmo defeito e não recebeu a correção.

## Sintoma

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

## Causa

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

| Item | Valor no aparelho testado |
| --- | --- |
| Chip | WCN3990, driver `ath10k_snoc` |
| Firmware | `qmi fw_version 0x101a832b`, de 21/12/2020 (do MIUI `V12.5.1.0.QFGMIXM`) |
| Kernel | `7.2.3-sdm660` |

A pista do TXBF veio de um comentário de SudosuBash na issue
[sdm660-mainline/linux#243](https://github.com/sdm660-mainline/linux/issues/243), que descreve
um sintoma parecido em outros aparelhos SDM630 e SDM660. A issue em si (autenticação que expira
depois de o roteador desassociar o aparelho) continua aberta, e este patch não foi testado
contra ela.

## Correção

[`kernel-7.2/0001-ath10k-wcn3990-sem-txbf-apos-vdev-down.patch`](../kernel-7.2/0001-ath10k-wcn3990-sem-txbf-apos-vdev-down.patch):
em `drivers/net/wireless/ath/ath10k/mac.c`, o `ath10k_bss_disassoc()` deixa de zerar o TXBF
quando o chip é WCN3990 e a interface é estação. O parâmetro volta a ser gravado na
associação seguinte, pelo `ath10k_bss_assoc()`.

O patch aplica sem conflito na branch `qcom-sdm660-7.2.y` do fork. Ele não foi enviado ao
sdm660-mainline.

## Teste

Kernel `7.2.3-sdm660`, variante Shenchao, em 15/11/2026. "Queda" é uma linha
`fatal error received` no log do kernel.

| Teste | Módulo original | Módulo com o patch |
| --- | --- | --- |
| Desligar e ligar o Wi-Fi (`nmcli radio wifi off` e `on`) | 2 quedas em 2 | 0 quedas em 4; reconecta sozinho |
| Andar pela casa, trocando entre os roteadores da malha (5 GHz e 2,4 GHz) | não repetido no 7.2.3; no `7.0.14`, 4 quedas em 16 s | 4 trocas, cada uma em menos de 1 s, 0 quedas, mesmo IP |
| Carregar o módulo instalado pelo `modprobe` | | carrega e conecta |

O log do debug confirma que, com o patch, o `set param 45` não é mais enviado depois do
`vdev down`.

**Não verificado:** perda total de sinal (sair do alcance de todos os roteadores), um boot
completo com o módulo novo, o kernel inteiro compilado com o patch (só o módulo foi
compilado), outros firmwares do WCN3990 e o kernel `7.0.14`.

O 5 GHz funcionou no `7.2.3` (conexão no canal 48).

## Como aplicar

### Compilando o kernel 7.2 inteiro

Siga [`kernel-7.2.md`](kernel-7.2.md) e, antes do `build-nura.sh`, aplique o patch no checkout
do kernel:

```bash
git -C linux apply ../kernel-7.2/0001-ath10k-wcn3990-sem-txbf-apos-vdev-down.patch
```

Ajuste o caminho do patch para onde este repositório estiver. Esse caminho não foi testado:
o aparelho recebeu só o módulo, como abaixo.

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

O `KBUILD_MODPOST_WARN=1` é preciso porque não há `vmlinux` nessa pasta. Antes de aplicar o
patch, compile uma vez e compare o `srcversion` com o do aparelho: se forem iguais, o checkout,
a config e o compilador batem.

```bash
modinfo build-wifi/drivers/net/wireless/ath/ath10k/ath10k_core.ko | grep srcversion
```

```bash
ssh <usuário>@172.16.42.1 cat /sys/module/ath10k_core/srcversion
```

Com o patch aplicado e o módulo recompilado, tire os símbolos de debug e comprima:

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
