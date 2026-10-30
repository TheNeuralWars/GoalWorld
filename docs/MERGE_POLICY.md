# MERGE POLICY — GoalWorld repo (canónico, vigente desde 2026-08-23)

## Merge authority

1. **Quien mergea: Hermes** — perfil `default` (orquestador) o `hermes-ceo`. Nadie más por defecto.
2. Antigravity y Nico **ya no son el merger por defecto**. Nico conserva veto/override en cualquier momento.
3. Los draft PRs los maneja Hermes: los marca ready y los mergea si pasan los criterios.
4. Aplica a TODOS los PRs, incluidos on-chain-adjacent. El freeze de **deploy/upgrade mainnet sigue intacto**: Hermes puede mergear código; desplegar a mainnet requiere orden explícita de Nico.

## Criterios mínimos antes de mergear

- `gh pr view <n>` → `mergeable=MERGEABLE`
- Review propia de Hermes (o Copilot no bloqueante)
- Build según área: `cargo check -p goalworld_program` / `npx tsc --noEmit`
- Sin secretos ni credenciales en el diff
- Merge vía `gh pr merge` contra origin — NUNCA `git merge` local si el working tree está sucio

## Prohibido

- `git add -A`, `stash -u`, checkout sobre árbol sucio
- Mergear un PR remoto cuyo diff ya no coincida con lo revisado
- Parchear contratos fuera de un PR dedicado (`agent:hermes-ceo`)
