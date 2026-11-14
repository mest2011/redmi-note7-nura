# Caixa principal do Redmi Note 7 no Nura

Sem estes patches, o som do Nura sai só pela saída de chamada: o kernel não declara o
amplificador da caixa. Com eles, a caixa toca e é a saída padrão.

## O chip

| Item | Encontrado |
| --- | --- |
| Amplificador | **MAX98937**, não MAX98927, TAS2557 nem TFA9894 |
| Ligação | `i2c@c1b6000` (`blsp_i2c6`), endereço `0x3a`, reset no GPIO 77, porta `PRI_MI2S_RX` |
| Alimentação | regulador `L6B`, 1,8 V |
| Prova | log `max98937` no MIUI e revisão `0x43` no registrador `0x600`, lida igual no Nura |

Sinais que enganam:

- O DTB do MIUI declara `tas2557@4c`, `tfa98xx@34` e `max98927@3a`. Só o último tem driver
  ligado, e mesmo o nome `max98927L` está errado.
- O MAX98937 tem outro mapa de registradores. O driver `max98927` do kernel carrega, liga
  tudo e fica mudo, com a revisão lida como `0x00`.

Registradores no MIUI com a caixa tocando, para comparar: `0x500=01`, `0x039=81`,
`0x023=40`, `0x025=42`, `0x026=08`, `0x027=88`, `0x018=03`. Com `tinyplay` direto no MIUI o
amplificador não liga; é preciso tocar por um app.

## O que os patches fazem

[`kernel/0001-lavender-alto-falante-max98937.patch`](../kernel/0001-lavender-alto-falante-max98937.patch):

1. Driver mínimo `sound/soc/codecs/max98937.c`, com a inicialização do driver GPL da Xiaomi.
2. Árvore do lavender: `blsp_i2c6`, regulador `L6B`, pinos e ligação `PRI_MI2S`, seguindo o
   Redmi Note 6 Pro (`tulip`).
3. `sdm660-internal.c`: informa o formato I2S ao amplificador.

[`pmaports/pmaports-lavender.diff`](../pmaports/pmaports-lavender.diff) liga
`CONFIG_SND_SOC_MAX98937=m` e acrescenta os patches aos `APKBUILD`.

[`ucm/0001-lavender-saida-speaker.patch`](../ucm/0001-lavender-saida-speaker.patch) cria a
saída `Speaker`, com prioridade 150: acima da de chamada, abaixo do fone. O `q6routing`
guarda uma porta por sessão, e desligar uma rota deixa a sessão sem porta
(`Routing not setup`). Por isso fica sempre uma rota ligada: `INT0`, trocada por `PRI`
enquanto a caixa estiver ativa.

## Serviço da troca de saída

O DSP só aplica a rota ao abrir a saída. Com algo tocando (o Chromium mantém a saída
aberta), trocar para a saída de chamada e voltar deixava a caixa muda.
[`scripts/redmi-audio-reabrir`](../scripts/redmi-audio-reabrir) olha o perfil a cada segundo
e reabre a saída quando ele muda. Precisa de `LC_ALL=C`, porque em português o `pactl`
traduz `Active Profile`.

No aparelho:

```bash
sudo install -m 755 scripts/redmi-audio-reabrir /usr/local/bin/redmi-audio-reabrir
```

```bash
sudo install -m 644 scripts/redmi-audio-reabrir.service /usr/lib/systemd/user/redmi-audio-reabrir.service
```

```bash
systemctl --user enable --now redmi-audio-reabrir.service
```

## Ganho

Sem a proteção DSM do Android, o driver começa no ganho seguro da Xiaomi (`Speaker` 1,
`Digital` 44). Os controles param nos valores do MIUI (`5` e `56`). No aparelho testado o
som ficou bom com `Speaker` 2 e `Digital` 48:

```bash
amixer -c0 cset name='Digital Volume' 48
```

```bash
sudo alsactl store
```

No Android, o DSM protege a caixa. Sem ele, suba o ganho aos poucos.

## Dicas

- O servidor de áudio é o PulseAudio. Para recarregar o UCM: `pulseaudio -k`. Reiniciar o
  PipeWire não adianta.
- Logo depois de ligar, o PulseAudio leva alguns segundos para criar a saída. Até lá aparece
  `auto_null`.
- Trocar a saída pelo terminal:

```bash
pactl set-card-profile alsa_card.platform-sound 'HiFi (Mic, Speaker)'
```

```bash
pactl set-card-profile alsa_card.platform-sound 'HiFi (Earpiece, Mic)'
```

## Testes

Medidos com um microfone externo, com tom de 500 Hz. O microfone do celular fica mudo no
Nura. São comparativos, sem posição fixa:

| Teste | Resultado |
| --- | --- |
| Silêncio | nível cerca de 1 |
| Caixa no ALSA direto, 8 s | de 13 a 51 |
| Caixa pelo PulseAudio, depois de reiniciar | de 9 a 17, saída padrão, sem erro de rota |
| Trocas com nada tocando | 5 de 5 sem perder a saída |
| Trocas com som contínuo, com o serviço | 4 de 4 trechos com som na caixa |
| Seletor do Phosh | troca funcionou |

**Não verificado:** a saída de chamada não passou do ruído do microfone externo; fone P2;
temperatura e uso longo; microfone do celular.
