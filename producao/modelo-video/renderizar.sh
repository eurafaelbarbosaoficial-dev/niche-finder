#!/bin/bash
# renderiza os capítulos em sequência (um por vez usa todos os núcleos)
cd "$(dirname "$0")"
for k in "$@"; do
  echo "$(date +%H:%M:%S) render $k"
  (cd $k && npx hyperframes render -q delivery -o renders/$k.mp4 --quiet > ../render-$k.log 2>&1) && echo "$(date +%H:%M:%S) ok $k" || echo "$(date +%H:%M:%S) ERRO $k"
done
