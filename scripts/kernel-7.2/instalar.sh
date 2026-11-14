#!/bin/sh
# Instala o kernel 7.2.3 de teste AO LADO do 7.0.14, sem apk e sem boot-deploy,
# e o deixa como padrão no extlinux. Não grava nenhuma partição do MIUI.
# Rodar como root, na pasta com vmlinuz-7.2, initramfs-7.2, o .dtb, o .tar dos
# módulos e SHA256SUMS: sudo sh ./instalar.sh
set -e
D=$(cd "$(dirname "$0")" && pwd)
C=/boot/extlinux/extlinux.conf
cd $D
sha256sum -c SHA256SUMS
grep -q 'deviceinfo_flash_kernel_on_update="false"' /etc/deviceinfo || { echo "PARE: sem a proteção em /etc/deviceinfo"; exit 1; }
sha256sum /dev/disk/by-partlabel/boot /dev/disk/by-partlabel/recovery > $D/particoes-antes.txt
cp vmlinuz-7.2 initramfs-7.2 sdm660-xiaomi-lavender-shenchao-7.2.dtb /boot/
tar -C /lib/modules -xf modules-7.2.3-sdm660.tar
[ -f $C.antes-7.2 ] || cp $C $C.antes-7.2
A=$(grep -m1 '^[[:space:]]*append' $C.antes-7.2)
{
	echo "timeout 1"
	echo "default teste72"
	grep '^menu' $C.antes-7.2 || true
	printf 'label teste72\n\tkernel /vmlinuz-7.2\n\tfdt /sdm660-xiaomi-lavender-shenchao-7.2.dtb\n\tinitrd /initramfs-7.2\n%s\n' "$A"
	sed -n '/^label/,$p' $C.antes-7.2
} > $C.novo
mv $C.novo $C
sync
sha256sum /dev/disk/by-partlabel/boot /dev/disk/by-partlabel/recovery | diff - $D/particoes-antes.txt && echo "partições do MIUI intocadas"
cat $C
echo "INSTALADO. Reiniciando em 5 s (vai cair no MIUI)."
sleep 5
reboot
