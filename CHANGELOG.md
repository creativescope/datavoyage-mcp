# Changelog

所有可见改动都记录在这里。时间均为 UTC。

格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/),版本遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### 计划

- README 加流程图与真实输出示例
- 国产 MCP 商店逐家提交
- 海外站 CreativeScope 的姊妹 skill 同步
- 新增 skill: TBD(看 issues)

## [1.0.0] - 2026-10-15

### 新增

- 首次公开发布。
- 5 个 Agent Skill 放在 `skills/`:
  - `datavoyage-creative-search` — 按游戏/关键词/国家/渠道搜索海外买量素材
  - `datavoyage-http-media-search` — 图搜视频/视频搜视频/以图搜视频多模态检索
  - `datavoyage-creative-related` — 从素材详情链接找相似广告与复用线索
  - `datavoyage-game-comparison` — 2 至 5 款游戏的买量规模横向对比
  - `datavoyage-store-charts` — Google Play 与 iPhone App Store 榜单查询与趋势
- 网关端点: `https://mcpapi.datavoyage.cn/mcp`(Streamable HTTP,OAuth 或 `AUTH_TOKEN` 环境变量)
- 覆盖渠道: Meta / Google / TikTok / Mintegral / Unity / AppLovin / ironSource / Liftoff / Pangle
- `server.json` 注册到官方 MCP Registry(`ai.datavoyage/mcp`)
- `glama.json` 申请 Glama 收录
- 14 个仓库 topics
- About 描述与 homepage 链接
- MIT `LICENSE`

[Unreleased]: https://github.com/creativescope/datavoyage-mcp/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/creativescope/datavoyage-mcp/releases/tag/v1.0.0
