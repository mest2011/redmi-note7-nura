# Dual boot MIUI + Nura no Redmi Note 7

O MIUI continua na partição `boot` e liga normal. O U-Boot do sdm660-mainline fica na
`recovery` e sobe o Nura de um cartão SD. Nada antes da `boot` é gravado: o fastboot da
Xiaomi continua sendo o caminho de resgate.

```
ABL (Xiaomi)
   ├─ ligar normal ──▶ boot = MIUI 12.5.1 com Magisk
   └─ modo recovery ─▶ recovery = U-Boot v2026.10-sdm660
                          └─ extlinux no cartão SD ──▶ Nura edge, Phosh
```

| Partição | Conteúdo |
| --- | --- |
| `boot` | MIUI com Magisk |
| `recovery` | U-Boot |
| `dtbo` | apagada: com ela, o U-Boot não sobe |
| `vbmeta` e cadeia de boot | intocadas |
| `userdata` | intocada |
| Cartão SD | Nura, raiz expandida para o cartão todo |

## Pré-requisitos

- Bootloader desbloqueado. No aparelho testado ele já vinha `unlocked:yes`, estado `orange`.
- Saber a variante do painel (`mdss_mdp.panel=` na linha de comando do kernel do MIUI).
  O aparelho testado é Shenchao, NT36672A.
- Um backup completo das partições **antes** de qualquer gravação, com hash.

## Como foi montado

1. **Backup sem TWRP.** Os TWRP oficiais 3.5.2, 3.6.2 e 3.7.0 reiniciam em `fastboot boot`
   neste firmware. Em vez disso: baixar a ROM oficial do mesmo build, conferir o MD5, passar
   a `boot` pelo Magisk e iniciá-la com `fastboot boot`, só na RAM. Com root, `dd` de todas
   as partições, com sha256 no aparelho e na cópia.
2. **Magisk 31.1:** o `Shell` precisa ser adicionado à mão na aba SuperUsuário (botão `+`).
   Sem isso, `su` nega na hora, sem pedido na tela.
3. **Imagem do Nura** no PC, com `pmbootstrap init` (xiaomi-lavender, variante certa) e
   `pmbootstrap install --no-sparse`. O pmbootstrap 3.12.1 ainda espera o remoto
   `gitlab.postmarketos.org` no clone do pmaports.
4. **Gravar o cartão** pelo próprio Android com root: `dd` em `/dev/block/mmcblk1`.
5. **Expandir a raiz**, que não expandiu sozinha: `sfdisk --relocate gpt-bak-std`, depois
   `sfdisk -N 2` e `resize2fs`, com o sistema no ar.
6. **Apagar a `dtbo`** (`fastboot erase dtbo`). Com a `dtbo` original, o ABL responde
   `Booting OKAY` ao `fastboot boot` do U-Boot e volta ao próprio fastboot, sem erro. Sem
   ela, o U-Boot sobe na hora, e o MIUI continua ligando, com toque, Wi-Fi, áudio, sensores
   e câmeras detectados.
7. **Testar o U-Boot em RAM** com `fastboot boot`, e só depois gravar na `recovery`. O menu
   do U-Boot não tem entrada para o Android (`bootmeths=extlinux efi_mgr`), por isso ele
   fica na `recovery`, e não na `boot`.
8. **Criar a proteção** `/etc/deviceinfo` no Nura antes de qualquer atualização (ver abaixo).

## Como alternar

- **Ir para o Nura:** `adb reboot recovery` no MIUI. `Power + Vol+` ao ligar deve fazer o
  mesmo, mas não foi testado.
- **Voltar ao MIUI:** reiniciar o Nura.
- **Tempo de troca:** cerca de 100 s até o Nura e de 90 a 160 s até o MIUI, em 3 ciclos.

Acesso pelo USB: o Nura cria uma rede em `172.16.42.1` (`ssh <usuário>@172.16.42.1`). Se o
Mac não pegar IPv4 depois de reconectar o cabo, use IPv6 de enlace: `ping6 ff02::1%<interface>`
e `ssh <usuário>@<fe80::...>%<interface>`.

## Incidente: o kernel gravou na `boot` do MIUI

Instalar um kernel com `apk add` no Nura rodou o `boot-deploy`, que gravou o `boot.img` do
Nura na partição `boot` do MIUI. A causa é `deviceinfo_flash_kernel_on_update="true"` no
`deviceinfo` do lavender. O MIUI só voltou depois de regravar a `boot` com Magisk a partir do
backup, com hash conferido antes e depois.

**Proteção:** [`scripts/etc/deviceinfo`](../scripts/etc/deviceinfo) em `/etc/deviceinfo`.
Foi testada rodando `mkinitfs` e instalando dois kernels: a `boot` não mudou. Uma imagem
nova do Nura não traz esse arquivo, então crie antes de qualquer `apk upgrade`.

## Voltar ao MIUI puro

No fastboot da Xiaomi, com as imagens do backup:

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

## Regras

- Não aceitar OTA do MIUI enquanto o dual boot existir.
- Nunca usar `fastboot oem lock` nem `flash_all_lock`.
- Não gravar `xbl`, `abl`, `tz`, `rpm`, `hyp` nem as cópias `*bak`.
- Backups e dumps têm IMEI, MAC e serial: nunca vão para o git.

## Riscos e pendências

- **`recovery` pode depender do Magisk.** O `install-recovery.sh` do MIUI existe, mas não
  restaurou a `recovery` em 4 boots. A hipótese, não testada, é que o patch dele falhe porque
  a `boot` está modificada. Tirar o Magisk pode desfazer o dual boot.
- **Depois de uma queda de energia o aparelho liga no MIUI**, não no Nura.
- **`modemst1`, `modemst2` e `persist` mudam com o uso**: o Android escreve nelas, e o
  `rmtfs` do Nura também pode. Sinal e IMEI com chip não foram testados.
- **Firewall sem efeito no Nura:** o kernel não tem nftables.
- **Wi-Fi só em 2,4 GHz.** Desconectar pode derrubar o modem até reiniciar.

## Dicas do dia a dia no Nura

- `setsid nohup` morre ao fechar o `ssh`: use `systemd-run`.
- O filtro de apps do Phosh (`app-filter-mode` adaptive) esconde apps sem
  `X-Purism-FormFactor`. Para Chromium e Brave, copie o `.desktop` para
  `~/.local/share/applications/` e acrescente a chave.

## Medições

| Teste | Resultado |
| --- | --- |
| Cartão SD (`fio`) | 42 MB/s de escrita, 79 MB/s de leitura; 1.448 e 654 IOPS em 4k aleatório |
| Docker nativo | `hello-world` com overlayfs e cgroup v2 |
| Coprocessadores | modem, ADSP e CDSP em `running` |
| Estabilidade das partições | `boot`, `recovery` e `dtbo` com hash igual depois de 3 ciclos de troca |
