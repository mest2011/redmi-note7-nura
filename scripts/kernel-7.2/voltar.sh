#!/bin/sh
# Volta o 7.0.14 a padrão no extlinux. Os arquivos do 7.2 ficam no /boot.
# Rodar como root: sudo sh ./voltar.sh
set -e
C=/boot/extlinux/extlinux.conf
cp $C.antes-7.2 $C
sync
cat $C
echo "7.0.14 de volta como padrão."
