# Freeze da GPU do Redmi Note 7 no Nura

## Sintoma

A tela congelava e só voltava reiniciando, com o `ssh` ainda funcionando. O kernel
registrava `timeout waiting to drain ringbuffer 0 rptr/wptr = 23/C`, depois
`hangcheck recover!` e `preemption timed out`. O `phoc` ficava em estado `D`, esperando a
GPU em `msm_gem_close`. Com o kernel `7.0.14` sem patches, 4 de 4 boots travaram entre 4 e
8 minutos.

## Causa provável

O mesmo erro, com os mesmos números, está descrito num patch do fork sdm660-mainline que a
tag `v7.0.14-sdm660` não tinha. Neste aparelho a GPU pode voltar do modo de economia sem ter
sido desligada de fato, e continua do ponteiro antigo. Outro patch trata o
`CP opcode error`, visto em um dos boots. Os patches não foram testados um a um.

## Correção

Três patches de Fabricio Akio, da branch `qcom-sdm660-7.2.y` do fork, sem alteração:

| Patch | Commit de origem | O que faz |
| --- | --- | --- |
| [`0002-a5xx-reset-ao-retomar.patch`](../kernel/0002-a5xx-reset-ao-retomar.patch) | [`be8062b9b02a`](https://github.com/sdm660-mainline/linux/commit/be8062b9b02a) | Reseta a GPU ao retomar, para ela não continuar do ponteiro antigo |
| [`0003-a5xx-latencia-cpu.patch`](../kernel/0003-a5xx-latencia-cpu.patch) | [`b63149ee8311`](https://github.com/sdm660-mainline/linux/commit/b63149ee8311) | Limita a latência da CPU enquanto a GPU está ligada (518 us na A512) |
| [`0004-a5xx-wptr-sob-trava.patch`](../kernel/0004-a5xx-wptr-sob-trava.patch) | [`45b54a7c4c87`](https://github.com/sdm660-mainline/linux/commit/45b54a7c4c87) | Escreve `CP_RB_WPTR` sob a trava, para não reexecutar comandos antigos |

Eles entram sem conflito sobre a tag `v7.0.14-sdm660`, nessa ordem. Ainda são `FROMLIST`:
foram enviados à lista do kernel. Ao subir para o 7.2 do fork, confira se o kernel já os traz.

## Teste

| Teste | Sem os patches | Com os patches (`7.0.14-r5`) |
| --- | --- | --- |
| Erro de GPU após ligar | 4 de 4 boots, entre 4 e 8 min | 0 em 34 min de boot |
| Chromium abrindo e fechando por 30 min | não medido | 0 erros, `phoc` respondendo no fim |
| Temperatura máxima | não medida | 54,6 °C |

**Não verificado:** a tela apagando e acendendo de forma explícita, uso por horas,
navegação real e consumo de bateria. Um kernel sem os patches chegou a rodar 76 min sem erro,
então 30 min limpos são um bom sinal, não prova definitiva.

## Como repetir o teste

[`scripts/teste-gpu/carga.sh`](../scripts/teste-gpu/carga.sh) abre e fecha um Chromium com
perfil separado por 30 min, para a GPU acordar e dormir.
[`scripts/teste-gpu/monitor.sh`](../scripts/teste-gpu/monitor.sh) grava a cada 30 s os erros
da GPU, os processos em estado `D` e o estado de energia.

Copie os dois para o celular e rode com `systemd-run`, porque `setsid nohup` morre ao fechar
o `ssh`:

```bash
systemd-run --user --unit=gpu-carga --collect sh ~/carga.sh
```

```bash
sudo systemd-run --unit=gpu-monitor --collect sh ~/monitor.sh
```

O log fica em `/var/log/teste-gpu.log`.
