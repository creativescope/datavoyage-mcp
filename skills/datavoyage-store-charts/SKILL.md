---
name: "datavoyage-store-charts"
display_name: "DataVoyage 海外手游榜单查询"
display_name_en: "DataVoyage Game Charts"
description: "查询海外手游 Google Play 与 iPhone App Store 免费榜、付费榜、畅销榜，查看游戏排名趋势和首次上榜游戏。自带浏览器登录授权，无需安装连接器。不用于买量热度榜、收入估算或素材搜索。"
description_zh: "查询海外手游免费榜、付费榜、畅销榜、排名趋势与首次上榜游戏。支持 Google Play 和 iPhone App Store，自带登录授权，无需安装连接器。"
description_en: "Explore overseas mobile game store charts, ranking trends and first-seen entries on Google Play and iPhone App Store. Includes browser sign-in without a marketplace connector."
version: "1.0.1"
author: "DataVoyage"
---

# DataVoyage 海外手游榜单查询

本 Skill 让助手用自然语言完成商店榜单查询。用户只需描述国家、商店和榜单需求；首次使用需本人在浏览器登录 DataVoyage 并授权。助手负责执行脚本和整理结果。通过内置脚本直接访问 DataVoyage MCP HTTP 服务，不依赖 WorkBuddy 连接器审核或安装。

## 必须遵守

- 必须使用本包脚本；禁止读取 WorkBuddy 或其他客户端的私有凭据缓存，禁止索取账号密码。
- 用户仅在官方浏览器页面登录。不得输出令牌、授权回调、缓存内容或完整授权 URL 到报告。
- 查询受账号权限和额度限制。只执行用户请求所需查询，禁止为诊断反复查询、自动翻完所有页或擅自扩大国家与日期范围。
- 免费榜、付费榜、畅销榜分别为 `0`、`1`、`2`。畅销排名不是收入金额，首次观测上榜不是游戏上线日期。
- 禁止把缺数据写成排名为零、把跨国家的最好名次拼成同一国家趋势，或编造游戏链接与结果。

## 适用范围与环境

适用于榜单、历史排名趋势、首次上榜查询。不适用于广告投放热度、下载收入估算或相似素材搜索。在 WorkBuddy 市场安装本技能后，使用技能安装目录内的 scripts 和 references；当前目录中的命令均相对于本 Skill 根目录，助手应自行定位，不依赖固定用户名或磁盘。

需要 Python 3.9+ 和 curl 7.70+。脚本只用 Python 标准库，无 pip 包、Node.js、ffmpeg 或 ffprobe 依赖。Windows 优先 `py -3`（没有时检测可用的 `python`）；macOS 使用 `python3`。缺少依赖时说明具体缺项，取得用户同意再安装，不要求新手配置 API Key、环境变量或连接器。

## 工作流程

1. 从用户问题识别查询类型（国家榜单 / 排名趋势 / 首次上榜）。缺少影响结果的条件时一次问清；单次国家榜单必须明确国家，不默认美国。参数细节与现成示例见[查询指引](references/query-guide.md)。
2. 直接运行正式入口完成查询。脚本会自动完成工具发现、身份校验和参数核对，**不需要先单独执行 --catalog**（该模式仅用于诊断）。查询参数以内联 JSON 传入：

   Windows：`py -3 scripts/charts.py --tool get_store_game_rank --args "{\"country_code\":\"US\",\"platform\":2,\"rank_type\":2,\"period\":\"day\",\"limit\":20,\"offset\":0}"`

   macOS：`python3 scripts/charts.py --tool get_store_game_rank --args '{"country_code":"US","platform":2,"rank_type":2,"period":"day","limit":20,"offset":0}'`

   参数较多或含特殊字符时，可把参数写为 UTF-8 JSON 文件后用 `--args-file query.json` 代替 `--args`；文件只含查询条件，不含凭据。趋势与首次上榜分别使用 `get_store_game_rank_trend`、`get_store_first_seen_games`；解析游戏身份用 `search_games` / `resolve_game_by_identifier`。参数必须匹配实时 schema，脚本会拒绝缺失必填项和未知参数。
3. 仅遇到 `LOGIN_REQUIRED` 或身份验证失败时运行 `py -3 scripts/auth.py login`（macOS 用 `python3`），告诉用户"请在打开的浏览器登录 DataVoyage 并授权，完成后我会继续查询"。登录进程最多等待 10 分钟：使用后台任务或足够长的执行窗口，保持进程存活。用户关闭或拒绝后停止，不反复打开浏览器。成功出现 `LOGIN_OK` 后用原参数重新执行入口命令。
4. 脚本在查询前打印结果路径并生成 `.attempt` 标记；超时或中断后先检查该路径。存在 result 文件就读取复用；只有标记没有结果时，说明结果未确认，不自动重试可能已计费的请求。输出路径已存在时按 `OUTPUT_EXISTS` 提示读取已保存结果，不重跑。
5. 读取脚本打印的 `output` 文件，先检查业务错误（`error_code`）、提示、实际日期及筛选条件，再按[结果呈现](references/output-format.md)组织答案。失败或中断时按[排障与续查](references/troubleshooting.md)处理。

使用助手支持的长任务/后台进程机制定期查看进度，不能因单次工具等待上限结束就重启查询；网络、代理和服务器也可能提前超时，不承诺固定总耗时。

按需加载参考资料：参数准备与解释使用[查询指引](references/query-guide.md)；结果呈现使用[结果呈现](references/output-format.md)；失败、中断或授权问题使用[排障与续查](references/troubleshooting.md)。

## 授权与失败处理

同一系统用户的本包与 DataVoyage HTTP 媒体搜索包共用自有授权存储，已有有效授权可复用；不读取连接器登录状态。已有 MCP 授权不等于本包获得授权。缓存保存在系统用户应用数据目录，脚本限制本地访问权限。不要读取或展示缓存。已有 `AUTH_TOKEN` 环境变量时脚本优先使用它，但新手无需设置。

401 或登录失效时引导重新授权；403 或额度不足时解释账号权限问题并停止；网络错误时保留结果路径，检查用户网络后再决定是否重试，不自动更改代理或关闭证书验证。脚本默认直连官方服务，企业网络只允许代理时需由用户确认网络策略。工具缺失时说明账号或服务尚未提供能力，不猜测接口。

用户明确要求退出时执行 `py -3 scripts/auth.py logout`（macOS 用 `python3`）。这会撤销并删除共享授权，媒体搜索包也需要重新登录；不会清除其他连接器缓存，也不会修改环境变量。

## 输出与验收

先说明商店、国家、榜单类型、实际数据日期和筛选口径，再展示排名、游戏及服务返回的链接。趋势区分国家、商店、分类和榜单；首次上榜标注"DataVoyage 首次观测"。只展示确实返回的字段，少于请求数量时如实说明。

验收必须满足：返回真实结果或明确失败原因；不泄露凭据；不把无数据当成功排名；不追加用户未请求的批量查询。用户提出"美国 iPhone 最新畅销榜前 20"时，应查询美国、平台 2、榜单 2，使用服务最新可用日期，并明确该日期。
