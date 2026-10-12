# Inbound SSH/HTTP broken by Tailscale exit node — root cause + fix

**Date:** 2026-10-12 · **Symptom:** every inbound port (22/80/443) timed out from the public
internet from ~19:04 UTC. `sshd` was running and listening; `fail2ban` and `ufw` were not
even installed. Nothing in the host firewall was at fault.

## Root cause

The VPS is a **Tailscale exit-node client** (exit node = Nico's Windows `win-90p10qeopqq` =
`100.101.209.8`), which is deliberate infra: it gives OmniRoute a residential egress IP so
Cloudflare 1010 (`browser_signature_banned`) stops banning groq / cerebras / cloudflare-ai /
mistral / sambanova.

That feature silently breaks **all inbound services**, because Tailscale's policy routing
sends every unmarked packet out the exit node:

```
5270: from all lookup 52        # table 52:  default dev tailscale0
```

```
$ ip route get 140.245.43.171
140.245.43.171 dev tailscale0 table 52 src 100.101.211.44
```

So a SYN arriving on `enp0s6` (dst `10.0.0.178`, public `89.168.20.135`) was answered by a
SYN-ACK leaving `dev tailscale0` with **source `100.101.211.44`**. The client never saw a
reply from the IP it dialed → TCP handshake never completed → timeout. Only SSH replies were
not the problem — port 80/443 (Docker-DNAT'd caddy) were equally dead, which is what made the
whole box look down.

Trigger timeline (`/var/log/omniroute_egress.log`):

```
2026-10-12T19:04:01Z SWITCH -> windows exit node (residential egress)
2026-10-12T19:04:05Z egress now via windows: 151.62.246.198
```

The egress monitor (`omniroute-egress-monitor.sh`, root cron 1 min) flipped the exit node on
when Nico's Windows machine came back online at 19:03:15. Inbound broke 45 s later. It is a
**known Tailscale limitation**, not a misconfiguration.

## Fix — policy routing for reply direction only

Mark **only** the reply direction of connections whose *original* destination was this host,
and route those via the main table. Outbound-initiated traffic (OmniRoute) is untouched and
keeps the residential egress.

```bash
# 1) locally generated replies (sshd and other host services)
iptables -t mangle -A OUTPUT   -s 10.0.0.178 -m conntrack --ctdir REPLY \
        -j MARK --set-mark 0x10000/0xff0000

# 2) forwarded replies (Docker DNAT'd caddy :80/:443). MUST be PREROUTING:
#    for forwarded packets the routing decision happens BEFORE the FORWARD chain,
#    so a mark set in FORWARD is applied too late to change the route.
iptables -t mangle -A PREROUTING -m conntrack --ctdir REPLY --ctorigdst 10.0.0.178 \
        -j MARK --set-mark 0x10000/0xff0000

# 3) marked packets -> main table (before Tailscale's 5270 lookup 52)
ip rule add fwmark 0x10000/0xff0000 lookup main priority 5205
```

Result:

```
$ ip route get 140.245.43.171 mark 0x10000
140.245.43.171 via 10.0.0.1 dev enp0s6 src 10.0.0.178 mark 0x10000   # inbound replies ✓
$ ip route get 140.245.43.171
140.245.43.171 dev tailscale0 table 52 src 100.101.211.44            # OmniRoute egress ✓
```

Mark `0x10000/0xff0000` is chosen so it does not collide with Tailscale's own
`0x80000/0xff0000` (rules 5210/5230/5250) or the `ts-postrouting` MASQUERADE
(`0x40000/0xff0000`).

## Persistence

`/usr/local/sbin/ensure-inbound-reply-routing.sh` (idempotent) + systemd unit
`inbound-reply-routing.service` (`After=network-pre.target tailscaled.service
netfilter-persistent.service`, `WantedBy=multi-user.target`). Re-run the script any time —
it never duplicates a rule.

## Pitfalls

- **A mark set in `mangle FORWARD` is useless** for this purpose: the route for forwarded
  packets is already chosen before FORWARD runs. Use `PREROUTING`.
- **`ufw` and `fail2ban` are NOT installed on this box.** The `ufw-*` chains visible in
  `iptables` are stale leftovers and are all placed *after* the `REJECT` at INPUT rule 17,
  i.e. dead. `ufw status` = `command not found`. Do not "fix" a firewall that is not there.
- INPUT rule 17 `REJECT icmp-host-prohibited` is the real default-deny; rules 18+ below it
  (8790, 4007, 8082, 8080, 3001, 3000…) are unreachable and never counted.
- The egress monitor will keep flipping the exit node on/off as Windows comes and goes. The
  fix is orthogonal — inbound stays healthy in both states.
- **Oracle Security List / NSG was NOT involved** — port 22 was always open there; the fix
  needed zero cloud-side changes.

## Verification (external, from 4–5 independent nodes)

| Port | Before | After |
|------|--------|-------|
| 22   | 0 OK / 4 timeout | **5 OK / 0 timeout** |
| 80   | 0 OK / 3 timeout | **5 OK / 0 timeout** |
| 443  | 0 OK / 4 timeout | **4 OK / 1 timeout** |

Backups before the change: `/data/backups/net/` (full `iptables-save`, `ip rule`, table 52)
and `/etc/iptables/rules.v4.bak-<ts>` / `rules.v6.bak-<ts>`.
