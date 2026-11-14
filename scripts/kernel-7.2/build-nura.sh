#!/bin/bash
# Kernel 7.2.y do sdm660-mainline com o driver da caixa, na config do Nura.
# Uso: KSRC=<checkout do kernel> T=<pasta de trabalho> ./build-nura.sh
set -eo pipefail
KSRC=${KSRC:?defina KSRC com o checkout do sdm660-mainline/linux (branch do PR 262)}
cd "$KSRC"
T=${T:-$KSRC/../teste72}; O=${O:-$KSRC/../build-nura}; B=${B:-$KSRC/../build-def}
# Em $T precisa estar config-7.0.14-nura (no celular: zcat /proc/config.gz).
M="make -s ARCH=arm64 LLVM=1 LOCALVERSION= -j$(nproc)"
mkdir -p $O $B
# B: defconfig do fork (7.2.y)
$M O=$B sdm660_defconfig
# A: config do Nura 7.0.14 levada ao 7.2
cp $T/config-7.0.14-nura $O/.config
$M O=$O olddefconfig
# soma: o que o defconfig liga e a config do Nura não
n=0
while IFS== read -r k v; do
  cur=$(grep -E "^$k=" $O/.config | cut -d= -f2- || true)
  if [ -z "$cur" ]; then ./scripts/config --file $O/.config --set-val "${k#CONFIG_}" "$v"; n=$((n+1)); echo "add $k=$v"; fi
done < <(grep -E "^CONFIG_[A-Z0-9_]+=(y|m)$" $B/.config)
./scripts/config --file $O/.config -m SND_SOC_MAX98937 -m SND_SOC_SM8250 -d LOCALVERSION_AUTO --set-str LOCALVERSION "-sdm660"
$M O=$O olddefconfig
echo "opções somadas: $n"
grep -E "^CONFIG_(SND_SOC_MAX98937|SND_SOC_SM8250|LOCALVERSION|MMC_SDHCI_MSM|MODULE_COMPRESS_ZSTD|DRM_MSM)=" $O/.config
$M O=$O kernelrelease
$M O=$O Image.gz modules qcom/sdm660-xiaomi-lavender-shenchao.dtb
rm -rf $T/stage && $M O=$O INSTALL_MOD_PATH=$T/stage INSTALL_MOD_STRIP=1 modules_install
cp $O/arch/arm64/boot/Image.gz $T/vmlinuz-7.2
cp $O/arch/arm64/boot/dts/qcom/sdm660-xiaomi-lavender-shenchao.dtb $T/sdm660-xiaomi-lavender-shenchao-7.2.dtb
ls -la $T/vmlinuz-7.2 $T/*.dtb; ls $T/stage/lib/modules/
find $T/stage -name "snd-soc-max98937*"
echo BUILD_NURA_OK
