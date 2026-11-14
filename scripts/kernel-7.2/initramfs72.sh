#!/bin/bash
# Monta o initramfs do 7.2 a partir do initramfs do Nura (7.0.14): troca só os
# módulos do kernel, mantendo scripts, firmware e a lista initramfs.load.
set -eo pipefail
T=${T:?defina T com a mesma pasta do build-nura.sh}
# Em $T precisa estar initramfs-7.0.14 (cópia do /boot/initramfs do Nura 7.0.14).
NOVO=$(ls $T/stage/lib/modules/)
VELHO=7.0.14-sdm660
R=$T/ird72
rm -rf $R && mkdir $R && cd $R
zstd -dc $T/initramfs-$VELHO | cpio -id 2>/dev/null
MV=usr/lib/modules
[ -d $MV/$VELHO ] || MV=lib/modules
nomes=$(find $MV/$VELHO -name '*.ko*' | sed 's|.*/||; s|\.ko.*||' | sort -u)
echo "módulos no initramfs velho: $(echo $nomes | wc -w)"
mkdir -p $MV/$NOVO
S=$T/stage/lib/modules/$NOVO
faltou=0
for m in $nomes $(cat $MV/initramfs.load 2>/dev/null); do
  # modprobe -D lista o módulo e as dependências, já com caminho
  if ! deps=$(modprobe -d $T/stage -S $NOVO -D "$m" 2>/dev/null); then
    grep -qw "$m" $S/modules.builtin 2>/dev/null && continue
    echo "FALTA: $m"; faltou=1; continue
  fi
  echo "$deps" | awk '/^insmod/{print $2}' | while read -r f; do
    rel=${f#$S/}; mkdir -p $MV/$NOVO/$(dirname "$rel"); cp "$f" $MV/$NOVO/"$rel"
  done
done
cp $S/modules.builtin* $S/modules.order $MV/$NOVO/ 2>/dev/null || true
rm -rf $MV/$VELHO
depmod -b $R -C /dev/null $NOVO 2>/dev/null || depmod -b $R $NOVO
echo "módulos no initramfs novo: $(find $MV/$NOVO -name '*.ko*' | wc -l)"
find . | sort | cpio -o -H newc 2>/dev/null | zstd -q -19 -T0 > $T/initramfs-7.2
ls -la $T/initramfs-7.2
[ $faltou = 0 ] && echo INITRAMFS_OK
