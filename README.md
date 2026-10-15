# DataVoyage MCP

**Mobile-game ad creative intelligence for the China market.**

DataVoyage (橙果数航) is a hosted [Model Context Protocol](https://modelcontextprotocol.io) server that gives your AI agent live access to overseas mobile-game advertising data — creative search, image/video similarity search, competitor comparison, and App Store / Google Play chart lookups.

This repository holds the public listing, connection metadata, and the ready-made **Agent Skills** for the DataVoyage MCP service. The hosted service itself is proprietary.

- Website: <https://www.datavoyage.cn>
- Get an API key / sign in: <https://www.datavoyage.cn>
- Dashboard: <https://lite.datavoyage.cn>

---

## What it does

| Capability | Description |
|---|---|
| **Creative search** | Find overseas mobile-game ad creatives by game, keyword, country, channel, format, language and duration |
| **Multi-modal search** | Upload an image or video and find visually similar ads (image→video, video→video) |
| **Related & reuse** | From one creative detail link, find similar ads and recorded reuse clues across games |
| **Competitor comparison** | Compare 2–5 games' ad scale (deduplicated creatives, ad plans, reinvestment) on consistent dates |
| **Store charts** | Google Play & iPhone App Store free / paid / grossing chart presence, ranking trends and first-seen entries |

Coverage spans the major ad channels used by Chinese game studios going overseas: Meta, Google, TikTok, Mintegral, Unity, AppLovin, ironSource, Liftoff, Pangle and more.

---

## Connecting

DataVoyage is a **remote** MCP server.

- Endpoint: `https://mcpapi.datavoyage.cn/mcp`
- Transport: Streamable HTTP
- Auth: OAuth (browser sign-in) or `AUTH_TOKEN` environment variable

### Via the Agent Skills (recommended)

Each skill ships with self-contained Python scripts that talk to the MCP HTTP service directly — no marketplace connector required, and no manual API-key setup for the end user. The user signs in once in their own browser.

Requirements: Python 3.9+ and curl 7.70+. Standard library only — no pip packages, Node.js or ffmpeg.

```bash
# Example: query the US iPhone grossing chart
py -3 scripts/charts.py --tool get_store_game_rank \
  --args '{"country_code":"US","platform":2,"rank_type":2,"period":"day","limit":20,"offset":0}'
```

### Via an MCP client

Point any MCP-compatible client at the endpoint above and complete the OAuth flow.

---

## Agent Skills

Installable [Agent Skills](https://agentskills.io) that teach your agent proven DataVoyage workflows. Copy a folder under [`skills/`](./skills) into your client (Claude, Codex, Cursor, or any Agent-Skills-compatible host).

| Skill | What it does |
|---|---|
| [`datavoyage-creative-search`](./skills/datavoyage-creative-search) | Search overseas mobile-game ad creatives by game, keyword, country, channel, format and duration |
| [`datavoyage-http-media-search`](./skills/datavoyage-http-media-search) | Upload an image or video to find visually similar ads (image→video, video→video) |
| [`datavoyage-creative-related`](./skills/datavoyage-creative-related) | From a creative detail link, find similar ads and recorded reuse clues |
| [`datavoyage-game-comparison`](./skills/datavoyage-game-comparison) | Compare ad scale across 2–5 games on consistent dates and metrics |
| [`datavoyage-store-charts`](./skills/datavoyage-store-charts) | Google Play & iPhone App Store chart presence, ranking trends and first-seen entries |

Each skill handles its own browser-based authorization on first use. No credentials are stored in this repository.

---

## Example prompts

- "Find UGC-style video ads for merge games running in the US on TikTok in the last 30 days."
- "Upload this screenshot and find ads that look like it."
- "Compare how hard Royal Match and Gossip Harbor are buying traffic this month."
- "Is Lordrush charting on the US iPhone free chart? Show the last 30 days."

---

## Data & compliance

- Creative intelligence is compiled from **publicly available ad placements** and concerns businesses and their public advertising activity, not private individuals.
- Ad creatives, game titles and trademarks belong to their respective owners.
- Rankings reflect public chart position — not revenue or download estimates.
- To request review or removal, contact <support@datavoyage.cn>.

---

## Links

- Website: <https://www.datavoyage.cn>
- Overseas product (CreativeScope): <https://creativescope.ai>
- Overseas MCP server: <https://github.com/creativescope/creativescope-mcp>
- Support: <support@datavoyage.cn>

## License

MIT — see [LICENSE](./LICENSE). This repository contains the public listing, connection metadata and Agent Skills for the DataVoyage MCP service; the hosted service itself is proprietary.
