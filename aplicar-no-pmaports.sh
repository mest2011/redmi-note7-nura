#!/bin/sh
# Aplica os patches do lavender num checkout do pmaports do Nura.
# Uso: ./aplicar-no-pmaports.sh <caminho-do-pmaports>
# Testado sobre o commit 31482d7d5233 do pmaports (kernel 7.0.14-r2, UCM r1).
set -eu
PM=${1:?uso: $0 <caminho-do-pmaports>}
AQUI=$(cd "$(dirname "$0")" && pwd)
K="$PM/device/testing/linux-postmarketos-qcom-sdm660"
U="$PM/device/testing/alsa-ucm-conf-qcom-sdm660"
[ -f "$K/APKBUILD" ] && [ -f "$U/APKBUILD" ] || { echo "pacotes do sdm660 não encontrados em $PM" >&2; exit 1; }

git -C "$PM" apply --check "$AQUI/pmaports/pmaports-lavender.diff"
git -C "$PM" apply "$AQUI/pmaports/pmaports-lavender.diff"
cp "$AQUI"/kernel/000*.patch "$K/"
cp "$AQUI"/ucm/0001-lavender-saida-speaker.patch "$U/"

# Confere se os patches copiados batem com o sha512sums dos APKBUILDs.
for d in "$K" "$U"; do
	( cd "$d" && awk '/^sha512sums="/{f=1;next} /^"/{f=0} f && /\.patch$/' APKBUILD | sha512sum -c - )
done
echo "Pronto. Compile com: pmbootstrap build --force --arch aarch64 linux-postmarketos-qcom-sdm660 alsa-ucm-conf-qcom-sdm660"
