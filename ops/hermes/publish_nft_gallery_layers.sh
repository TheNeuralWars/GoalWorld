#!/usr/bin/env bash
# Build layered NFT gallery assets + sync data for webapp
set -euo pipefail
REPO="${goalworld_REPO_PATH:-/data/apps/goalworld}"
cd "$REPO"

mkdir -p goalworld_webapp/public/assets/data
cp -f docs/assets/data/players.json goalworld_webapp/public/assets/data/players.json

python3 ops/hermes/build_nft_gallery_v71.py "$@"

# Optional: rsync composed to API static if Caddy mount exists
if [[ -d /home/ubuntu/scratch/goalworld-pilot/v71_grok ]]; then
  mkdir -p /home/ubuntu/scratch/goalworld-pilot/nft_gallery/composed
  rsync -a docs/assets/img/nfts/composed/ /home/ubuntu/scratch/goalworld-pilot/nft_gallery/composed/ 2>/dev/null || true
  rsync -a docs/assets/img/nfts/transparent/ /home/ubuntu/scratch/goalworld-pilot/nft_gallery/transparent/ 2>/dev/null || true
  cp -f docs/assets/data/nft_gallery_manifest.json /home/ubuntu/scratch/goalworld-pilot/nft_gallery/manifest.json
fi

echo "NFT gallery build complete."