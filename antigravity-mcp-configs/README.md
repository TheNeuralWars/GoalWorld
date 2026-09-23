# MCP Configs para Antigravity (Windows)

Este paquete contiene las configuraciones de MCP servers para usar en Antigravity.

## Archivos incluidos

1. **hermes-config.yaml** — Configuración completa de Hermes con MCP servers
2. **mcp-goalchain-ops.py** — MCP server de GoalWorld Ops (status, economy, onchain)
3. **hermes-context.sh** — Script de contexto de Hermes

## MCP Servers configurados

| Server | Tipo | URL/Command |
|--------|------|-------------|
| agent-reach | HTTP | https://mcp.exa.ai/mcp |
| gbrain | STDIO | gbrain serve |
| goalworld-ops | STDIO | python mcp-goalchain-ops.py |
| codebase-memory-mcp | STDIO | codebase-memory-mcp |
| filesystem | STDIO | npx @modelcontextprotocol/server-filesystem |

## Uso en Antigravity

1. Copiar estos archivos a tu proyecto en Windows
2. En Antigravity, configurar MCP servers apuntando a estos paths
3. Para agent-reach: usar URL https://mcp.exa.ai/mcp
4. Para gbrain: instalar gbrain en Windows y usar `gbrain serve`
5. Para goalworld-ops: requiere Python + dependencias del repo

## Requisitos

- Python 3.11+
- Node.js 18+
- Bun (para gbrain)
- Cuenta de Exa (para agent-reach)

## Nota importante

Los MCP servers en config.yaml usan paths del VPS (/data/apps/GoalWorld, etc.)
Deberás adaptar estos paths a tu estructura local de Windows.
