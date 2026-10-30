# goalworld.fun 404: fix log (2026-09-25)

Operator: Grok Bot (executor), on Nico's instruction. Not committed.

## Symptom
The site returned 404 through Cloudflare from 05:00 UTC. `GoalChain/_site_public` (bind-mounted into
`twenty-caddy` as `/srv/goalworld`) had no `index.html` or `goalworld.html`. `assets/film/improve_20260915/`
held only `index.html` and the README. `improve_20260914/` was missing.

## Root cause
Two runs of `GoalChain/scripts/pages/deploy_origin.sh` overlapped on the shared scratch dir `_site_public.new`.
- **Run A**: the 5-min user timer `goalworld-origin-deploy.timer`, started 05:00:20 UTC.
- **Run B**: a manual run after Hermes CEO committed `0dfebea0` at 05:00:01.

Run A's `rm -rf _site_public.new` deleted files while Run B was staging into that dir. Run A then died with
`rm: cannot remove '.../_site_public.new/assets/film/improve_20260915': Directory not empty`.
Run B then did `rsync -a --delete` of the partial tree into `_site_public` and wrote `.deploy-last.head`
(05:00:40) = HEAD. Every later timer run printed "no docs changes since 0dfebea0" and exited, so nothing
repaired the tree.

## Changes
1. Backup (before any change): `/data/backups/goalworld-site/`
   - `_site_public-20260925T055629Z-broken/` (1.5 GB, the broken served tree)
   - `deploy_origin.sh.20260925T055629Z`, `deploy-last.head.20260925T055629Z`
2. `GoalChain/scripts/pages/deploy_origin.sh` (uncommitted, +18/-1):
   - `flock -w 900` on `$(git rev-parse --git-dir)/deploy-origin.lock`, so the timer and manual runs are serialized.
     The lock file lives in .git, so it adds no untracked noise.
   - New sanity gate: refuses to `rsync --delete` if the staged tree lacks a non-empty `index.html` or `goalworld.html`.
   - New `DEPLOY_FORCE=1` escape hatch that restages even when HEAD == last deployed. Use it to repair a broken tree.
3. Restaged: `DEPLOY_FORCE=1 bash scripts/pages/deploy_origin.sh`. Result: guard OK, "restaged 0dfebea0" at 05:59:20 UTC,
   `_site_public` is 2.9 GB, both film dirs are complete. The next timer run (06:02 UTC) exited cleanly under systemd.

## Verification (external, via Cloudflare)
| URL | Result |
|---|---|
| https://goalworld.fun/ | 200 |
| https://goalworld.fun/goalworld.html | 200 |
| https://goalworld.fun/assets/film/improve_20260915/ | 200 |
| .../improve_20260915/FC_full_conform_v3_ax.mp4 | 200 (237,487,103 B), Range → 206 video/mp4 |
| https://goalworld.fun/assets/film/improve_20260914/ | 200 |
| .../improve_20260914/FC_full_conform_v1.mp4 | Range → 206 video/mp4 |

## goalchain.fun / postiz timeouts: diagnosed, NOT fixed
- Caddy on the host serves both. Checked locally: `goalchain.fun` → 200 and `postiz.*` → 307 (the postiz login redirect).
- Only goalworld.fun goes through the cloudflared tunnel. goalchain.fun is Cloudflare-proxied to the public IP
  89.168.20.135, and postiz.goalchain.fun / postiz.goalworld.fun resolve DNS-only to that IP.
- Inbound SYNs to 89.168.20.135:443 never reach the INPUT chain (counters stay flat).
  Cause: the VPS is using **Tailscale exit node `win-90p10qeopqq` (100.101.209.8)** with RouteAll=true.
  Its egress IP is 151.62.152.63 and the default route goes via tailscale0 (table 52).
  With `rp_filter=2`, the asymmetric path drops public inbound traffic.
- Fixing this means changing the exit-node setting. That is out of scope under the rules for this task, so it was left for Nico.

## Left for Nico
- Decide on the exit node. It is active now against the standing rule "never re-enable WIN-90P10QEOPQQ".
  All VPS egress currently goes through that Windows PC. Clearing it (e.g. `sudo tailscale set --exit-node=`)
  should bring goalchain.fun and postiz back. Also find out who or what re-enabled it.
- Commit the deploy_origin.sh change on GoalChain (dirty tree: stage only that path).
- Any agent that deploys manually should keep calling `scripts/pages/deploy_origin.sh`, so it takes the lock,
  and never stage into `_site_public.new` by hand.
- Delete the backup in `/data/backups/goalworld-site/` once the site has stayed stable.
