# Infrastructure Blockers

## Critical
- **Legal entity**: Required for Google/MS/AWS/NVIDIA startup credits (P0).
- **LinkedIn**: Blocker #2 for startup credits.

## Operational
- **gbrain-sync**: ✅ Active — systemd service on `:8648`, timer every 5 min. No action needed.
- **hermes-api-server**: ✅ Active — pm2 id=12, port `:3001`, health confirmed. Persisted via `pm2 save`.

## DNS
- **crm.goalworld.fun**: Missing CNAME record.
  - **Impact**: CRM UI unavailable.
  - **Solution**: Add CNAME in Cloudflare → `cname.vercel-dns.com` (proxy enabled).