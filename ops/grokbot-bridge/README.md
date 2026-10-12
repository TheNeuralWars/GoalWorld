# Hermes ↔ Grok Bot bridge (goalchain ↔ jefe-gabinete)

Two ways for Grok Bot to drive this Hermes host, both over **Tailscale only**.
Built from `shagghiesuperstar/hermes-grok-bridge`.

| Method | Works when | Endpoint |
|---|---|---|
| **SSH relay** | today — needs only SSH access | `ubuntu@100.101.211.44` → `hermes -z` |
| **Native API** | once the API server is enabled (one gateway reload) | `http://100.101.211.44:8642/v1` |

Neither needs inbound access to the Hermes host: the relay SSHs **out**, the API
client dials the **tailnet IP**. No Funnel, no public bind.

## How to fetch this bundle (from the Grokbot host)

```bash
scp -r ubuntu@100.101.211.44:/data/apps/GoalWorld/ops/grokbot-bridge ~/grokbot-bridge
cd ~/grokbot-bridge && bash setup-grokbot.sh relay
```

`setup-grokbot.sh relay` clones the bridge repo on the Grokbot side, prints the
MCP config to paste into the Grok Bot app, and runs a live smoke test.

For the API method:

```bash
scp ubuntu@100.101.211.44:/data/apps/GoalWorld/ops/grokbot-bridge/.staged/hermes-api.env \
    ~/.hermes-api-100_101_211_44.env
bash setup-grokbot.sh api
```

## Security rules (from the bridge repo, enforced here)

- **Tailscale only.** The API server binds `100.101.211.44`, never `0.0.0.0`,
  and the host firewall drops non-tailnet traffic to `:8642` / `:8645`.
- **Never commit a key.** The API key lives in a `600` file on each side.
  The repo is public, and a key that reached it before had to be rotated.
- **Do not let a Grok bot write into Hermes memory plugins** (Hindsight, LCM,
  Graphiti, Omega) without an explicit memory plan.
- **Per-host identity.** Grokbot holds its own OmniRoute key
  (`grokbot-jefe-gabinete`, `self:usage` only — it cannot administer keys) so
  usage is attributable and a compromise is scoped. The fleet's own key is
  separate (`hermes-fleet`).
- Account-wide MCP tools are visible to all of a user's Grok Bots — confine each
  identity bot in its system prompt.

## What "healthy" looks like

- `setup-grokbot.sh relay` prints `RELAY_OK` from the far side.
- `/health` returns 200 and `/v1/models` returns a model list **with** the
  Authorization header, 401 without it.

`/v1/models` on the *far* side is not a useful probe for whether the API server
is up: it answers 200 regardless of the key, and so does
`/v1/chat/completions`. Treat `/health` and `/api/*` as authoritative.
