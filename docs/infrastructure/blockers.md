# Infrastructure Blockers

## Critical
- **Legal entity**: Required for Google/MS/AWS/NVIDIA startup credits (P0).
- **LinkedIn**: Blocker #2 for startup credits.

## Operational
- **gbrain-sync daemon**: Not running (no service/pm2 entry).
  - **Impact**: Obsidian→gBrain sync broken.
  - **Solution**: Install via `pip install gbrain-core` and configure systemd/pm2.
- **api-server**: Not registered as service/pm2.
  - **Impact**: `goalworld.fun/api` endpoints unavailable.
  - **Solution**: Register with `pm2 start "node /path/to/server.js" --name hermes-api-server`.

## DNS
- **crm.goalworld.fun**: Missing CNAME record.
  - **Impact**: CRM UI unavailable.
  - **Solution**: Add CNAME in Cloudflare → `cname.vercel-dns.com` (proxy enabled).