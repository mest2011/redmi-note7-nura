# Câmeras do Redmi Note 7 no Nura

As três câmeras funcionam no kernel `7.2.3` do fork, com autofoco na principal:

| Câmera | Sensor | Modos | Observação |
| --- | --- | --- | --- |
| Principal (traseira) | Samsung S5KGM1 | 4000x3000, 2000x1500 | autofoco pelo motor DW9800K |
| Frontal | OmniVision OV13855 | 4224x3136, 2112x1568 | foco fixo |
| Profundidade (traseira) | Samsung S5K5E8 | 2592x1944, 1296x972 | foco fixo |

O `libcamera` lista as três (`cam -l`), o PipeWire as expõe como fontes e o app Câmera (Snapshot) mostra a imagem em pé. Tudo passa pelo ISP por software do `libcamera`, porque o ISP da Qualcomm não tem driver no kernel mainline.

O que falta: toque para focar, flash, o modo de 48 MP da principal e a matriz de cor medida da frontal. Detalhes em [Limites](#limites).

Vale para o kernel `7.2.3` do fork (ver [`kernel-7.2.md`](kernel-7.2.md)). O `7.0.14` empacotado pelo Nura não recebeu nada disto.

## O que estava faltando

Sem estes patches, o `camss` do SDM660 nem chegava a entregar um quadro, e o lavender não tinha as câmeras no device tree.

### Kernel

| Patch | O que faz |
| --- | --- |
| [`0003`](../kernel-7.2/0003-camss-sdm660-ispif-mux-e-clock-do-csiphy.patch) | O `camss` cria o ISPIF e mapeia o mux de clock do CSIPHY só para 8x16/8x39/8x53/8x96 e esquecia o SDM660: nenhum quadro chegava (`VFE sof timeout`, até com o padrão de teste do CSID). O clock do CSIPHY também ficava em 19,2 MHz por falta de frequência na tabela, e só chegavam as primeiras linhas de cada quadro. |
| [`0004`](../kernel-7.2/0004-camss-vfe-conta-o-vinculo-do-dominio-de-energia.patch) | O reset do ISPIF liga e desliga o domínio de energia da VFE pelo mesmo ponteiro que a VFE usa e o zera: parar a captura derrubava o kernel (ponteiro nulo em `vfe_pm_domain_off`). |
| [`0005`](../kernel-7.2/0005-dts-sdm630-camss-com-dominio-top.patch) | O `camss` precisa do domínio `CAMSS_TOP_GDSC`; sem ele, `camss_top_ahb_clk status stuck at 'off'` e o barramento das câmeras (CCI) não funciona. |
| [`0006`](../kernel-7.2/0006-media-i2c-s5kgm1-ov13855-s5k5e8.patch) | Drivers dos três sensores. |
| [`0007`](../kernel-7.2/0007-dts-lavender-cameras.patch) | Device tree do lavender: reguladores, CCI, `camss`, os três sensores e o motor de foco. |

As opções do kernel estão em [`cameras.config`](../kernel-7.2/cameras.config).

Os drivers dos sensores não foram escritos à mão. O [`gen_drivers.py`](../scripts/cameras/gen_drivers.py) lê as tabelas de registradores das bibliotecas de câmera do MIUI (`libmmcamera_lavender_*.so`, da partição `vendor`) e gera os três arquivos a partir de um modelo baseado no `s5kjn1.c`. As bibliotecas não estão neste repositório. Por isso os drivers não servem para enviar ao kernel do jeito que estão: as tabelas são dados do fabricante, e faltam os bindings.

As ligações (endereço no CCI, CSIPHY, MCLK, GPIOs de reset e de energia) vieram do device tree do MIUI, tirado da `boot.img`:

| Câmera | CCI | CSIPHY | MCLK | Reset | Outros |
| --- | --- | --- | --- | --- | --- |
| Principal | 1, `0x10` | 1 | 3 (gpio35) | gpio52 | AVDD gpio62, DVDD `pm660l` gpio4, VAF gpio50; motor de foco em CCI1 `0x0c` |
| Frontal | 1, `0x36` | 2 | 1 (gpio33) | gpio47 | powerdown gpio45, AVDD gpio46, DVDD `pm660l` gpio3 |
| Profundidade | 0, `0x18` | 0 | 0 (gpio32) | gpio48 | mesmas fontes da frontal |

Três detalhes que custaram tempo:

- **Rotação.** O MIUI informa `qcom,mount-angle` (90 na principal, 270 na frontal) no sentido do Android, horário. A propriedade `rotation` do Linux é anti-horária: é `360 − mount-angle`. Com os valores do MIUI, a imagem aparecia de ponta-cabeça no app.
- **Ordem das cores da profundidade.** A biblioteca indica GBRG, mas o sensor entrega GRBG: com GBRG, o vermelho e o azul se trocavam.
- **O motor de foco precisa do L11A.** O regulador de 1,8 V de I/O das câmeras também alimenta os pull-ups do CCI. Com todos os sensores desligados, o motor dava `queue 0 timeout`. O `0007` deixa o L11A sempre ligado.

### libcamera

O `libcamera` 0.8.0 do Nura não sabe focar com o ISP por software. A pasta [`libcamera/`](../libcamera/) tem o que foi preciso:

| Arquivo | Autor | O que faz |
| --- | --- | --- |
| `af-0003` a `af-0010` | Milan Zamazal (Red Hat) | Série RFC "Autofocus basics for software ISP" v2, enviada à lista do libcamera em outubro de 2026 ([Patchwork](https://patchwork.libcamera.org/project/libcamera/list/?series=6324)). Leva o algoritmo de foco do IPU3 para o `libipa` e liga o motor da lente ao pipeline `simple`. |
| `af-0011` | este repositório | A série cria o campo de nitidez, mas não o calcula: ele ficava em 0 e a lente parava no fim do curso. Este patch mede a nitidez nos formatos Bayer de 10 bits empacotados (diferença entre verdes vizinhos, na metade central, normalizada pelo brilho). |
| [`APKBUILD.diff`](../libcamera/APKBUILD.diff) | este repositório | Acrescenta os patches ao pacote `temp/libcamera` do pmaports (`pkgrel=3`). |
| [`tuning/`](../libcamera/tuning/) | este repositório | Ajustes do ISP por software para os três sensores. |

Os ajustes têm:

- **Nível de preto** de cada sensor.
- **Matriz de cor** medida fotografando uma carta de 24 cores mostrada na tela de um notebook ([`carta.html`](../scripts/cameras/carta.html) e [`ccm.py`](../scripts/cameras/ccm.py)). Ela reduziu o erro médio de cor (ΔE) de 23 para 11. A da frontal é provisória.
- **Exposição em etapas:** primeiro o ganho sobe até 4x a 1/30 s; só depois o quadro se alonga até 1/10 s.
- **Autofoco** (`Af`), só na principal.

Esses sensores não têm `CameraSensorHelper` no `libcamera`, então os ganhos do arquivo estão no código do registrador (S5K: 32 = 1x; OV13855: 128 = 1x).

## Como aplicar

### Kernel

Siga [`kernel-7.2.md`](kernel-7.2.md). Antes do `build-nura.sh`, aplique os patches em ordem no checkout do kernel:

```bash
git -C linux apply ../kernel-7.2/000[1-7]-*.patch
```

Ao compilar, passe as opções das câmeras para o script:

```bash
EXTRA_CONFIG=kernel-7.2/cameras.config KSRC=$PWD/linux T=$PWD/teste72 ./scripts/kernel-7.2/build-nura.sh
```

Ajuste os caminhos para onde estiver o repositório. Os sete aplicam sem conflito na branch `qcom-sdm660-7.2.y` e na `lavender-max98937`. O aparelho testado recebeu só o device tree e os módulos (`qcom-camss`, `i2c-qcom-cci`, `v4l2-cci`, os três sensores e `dw9719`), compilados um a um como em [`wifi.md`](wifi.md#só-o-módulo-com-o-723-já-instalado). O `qcom-camss` substitui o do pacote, então vai para `/lib/modules/7.2.3-sdm660/updates/`. Os outros vão para `extra/`, seguidos de `sudo depmod 7.2.3-sdm660`. O kernel inteiro com os sete patches não foi compilado.

O DTB novo entra numa linha `fdt` própria no `/boot/extlinux/extlinux.conf`, ao lado da anterior, para ter como voltar.

A principal precisa ser a primeira câmera traseira. Sem isto, a de profundidade carrega antes e vira a câmera padrão:

```bash
printf 'softdep s5kgm1 pre: qcom-camss\nsoftdep ov13855 pre: s5kgm1\nsoftdep s5k5e8 pre: ov13855\n' | sudo tee /etc/modprobe.d/redmi-cameras.conf
```

### libcamera

No PC, num checkout do pmaports com o `pmbootstrap` configurado para o lavender:

```bash
cp libcamera/af-*.patch pmaports/temp/libcamera/
```

```bash
git -C pmaports apply ../libcamera/APKBUILD.diff
```

```bash
pmbootstrap build libcamera --arch aarch64 --force
```

Leva uns 6 minutos com compilação cruzada. Copie para o celular os pacotes `libcamera`, `libcamera-ipa` e `libcamera-tools` gerados em `packages/edge/aarch64/` e instale:

```bash
sudo apk add --allow-untrusted ./libcamera-99990.8.0-r3.apk ./libcamera-ipa-99990.8.0-r3.apk ./libcamera-tools-99990.8.0-r3.apk
```

Os ajustes vão para `/etc`, que o `libcamera` lê antes de `/usr/share`:

```bash
sudo mkdir -p /etc/libcamera/ipa/softisp
```

```bash
sudo cp libcamera/tuning/*.yaml /etc/libcamera/ipa/softisp/
```

O usuário precisa estar no grupo `video`. Como root, o `cam` tenta reservar memória contígua (32 MB) e falha.

## Como conferir

Os três sensores responderam no boot:

```bash
sudo dmesg | grep "chip id"
```

Devem aparecer `0x8d1`, `0xd855` e `0x5e80`. Câmeras e rotação:

```bash
cam -l
```

```bash
cam -c1 -p | grep -E "Rotation|Location"
```

A principal deve dizer `Rotation = 270` e `Location = 1 (Back)`; a frontal, `Rotation = 90`. Para ver o foco trabalhando, aponte a principal para algo com textura e acompanhe a lente (0 a 1023):

```bash
cam -c1 -C100 >/dev/null & sleep 6; v4l2-ctl -d $(media-ctl -e "dw9719 3-000c") -C focus_absolute
```

## Testado

17/11/2026, no aparelho descrito no [README](../README.md#estado-novembro-de-2026), com o kernel `7.2.3` e o `libcamera` `99990.8.0-r3`:

| Teste | Resultado |
| --- | --- |
| Identificação no boot | os três sensores respondem; o motor de foco registra como `v4l-subdev` |
| Quadros brutos | completos nas três câmeras, em todos os modos |
| `libcamera` (`cam`) | as três capturam; 30 fps com luz, até 10 fps no escuro |
| Exposição no escuro | a exposição chega a 100 ms; antes ficava presa em 33 ms e a imagem saía escura |
| Cor | a carta de 24 cores sai próxima das cores reais na principal e na profundidade (erro médio ΔE 11) |
| Autofoco | a nitidez medida varia de 1,15 a 3,28 conforme a lente, e a busca para sempre no mesmo ponto (627 de 1023, carta a ~15 cm) |
| PipeWire e app Câmera | as três aparecem como fontes; a imagem fica em pé |

## Limites

- **Toque para focar:** não existe. O algoritmo foca o centro da imagem e refaz a busca quando a cena muda.
- **Cor sob luz misturada:** o balanço de branco é do tipo "mundo cinza". Com luz misturada (lâmpada e tela) ou uma cena muito colorida, os cinzas puxam para verde ou rosa.
- **Frontal:** a matriz de cor é provisória, uma média suavizada das outras duas.
- **Flash e 48 MP:** sem flash. A principal entrega 12 MP; o modo de 48 MP (quad Bayer) não foi tentado.
- **Velocidade:** a exposição automática leva alguns segundos para acertar. O ISP por software roda a 10 a 30 fps, conforme a luz.
- **Atualização do sistema:** um `apk upgrade` que traga um `libcamera` mais novo do Nura troca o pacote com autofoco. Será preciso recompilar com a série.

## Como voltar

1. Escolha a entrada anterior no `extlinux.conf` (o DTB antigo não tem câmeras).
2. Reinstale o `libcamera` do repositório:

```bash
sudo apk add libcamera=99990.8.0-r1 libcamera-ipa=99990.8.0-r1 libcamera-tools=99990.8.0-r1
```

## Dica: reiniciar direto no Nura

O reinício normal cai no MIUI, e era preciso `adb reboot recovery` pelo cabo para voltar. O PMIC do lavender tem o modo `recovery`, que faz o bootloader abrir a partição `recovery` (o U-Boot), e o U-Boot sobe o Nura:

```bash
sudo systemctl reboot --reboot-argument=recovery
```
