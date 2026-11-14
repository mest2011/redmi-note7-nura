#!/bin/sh
# Registra a cada 30 s erros da GPU, processos presos e ciclos de energia, por 31 min.
# Rode como root. O log vai para o primeiro argumento ou /var/log/teste-gpu.log.
L=${1:-/var/log/teste-gpu.log}; : > "$L"; G=/sys/bus/platform/devices/5000000.gpu/power
F=$(( $(date +%s) + 1860 ))
while [ $(date +%s) -lt $F ]; do
  e=$(journalctl -b 0 -k --no-pager | grep -cE 'gpu fault|hangcheck|preemption timed out|timeout waiting to drain|timeout waiting for space|opcode error')
  d=$(for p in /proc/[0-9]*; do [ "$(awk '/^State/{print $2}' $p/status 2>/dev/null)" = D ] && cat $p/comm; done | tr '\n' ' ')
  echo "$(date +%T) up=$(cut -d. -f1 /proc/uptime) erros=$e D=[$d] gpu=$(cat $G/runtime_status) susp_ms=$(cat $G/runtime_suspended_time) ativo_ms=$(cat $G/runtime_active_time) f=$(cat /sys/class/devfreq/5000000.gpu/cur_freq) gpuT=$(cat /sys/class/thermal/thermal_zone*/temp 2>/dev/null | sort -n | tail -1)" >> "$L"
  sleep 30
done
echo FIM >> "$L"
