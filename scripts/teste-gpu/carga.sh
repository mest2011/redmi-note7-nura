#!/bin/sh
# Abre e fecha um Chromium isolado por 30 min para a GPU acordar e dormir.
# Rode como o usuário da sessão Phosh, com systemd-run --user (ver docs/gpu.md).
R=${XDG_RUNTIME_DIR:-/run/user/$(id -u)}
export XDG_RUNTIME_DIR=$R WAYLAND_DISPLAY=${WAYLAND_DISPLAY:-wayland-0} DBUS_SESSION_BUS_ADDRESS=unix:path=$R/bus
U='data:text/html,<body style="margin:0;background:%23111"><div style="width:60vw;height:60vw;background:%234af;animation:g 1s linear infinite"></div><style>@keyframes g{to{transform:rotate(360deg)}}</style>'
F=$(( $(date +%s) + 1800 ))
while [ $(date +%s) -lt $F ]; do
  chromium --ozone-platform=wayland --user-data-dir=/tmp/gpu-teste --no-first-run --new-window "$U" >/dev/null 2>&1 &
  P=$!; sleep 40; kill $P 2>/dev/null; sleep 3; pkill -f 'user-data-dir=/tmp/gpu-teste' 2>/dev/null; sleep 17
done
rm -rf /tmp/gpu-teste
