---
name: "datavoyage-game-comparison"
display_name: "橙果数航 海外游戏竞品投放对比"
display_name_en: "DataVoyage Competitor Advertising Comparison"
description: "在相同日期和筛选口径下对比 2 至 5 款海外游戏的素材量、广告计划与复投规模，回答这几款谁投得更猛、投放量差多少；自带浏览器登录授权，无需安装连接器。不用于收入或 ROI 比较。"
description_zh: "对比 2 至 5 款海外游戏的买量规模：去重素材数、广告计划数、复投力度，同一日期口径横向比较，覆盖手游为主的出海游戏广告市场。自带登录授权，无需安装连接器。"
description_en: "Compare advertising scale across two to five overseas games: creative volume, ad plans and reinvestment, using consistent dates and metrics. Includes browser sign-in without a marketplace connector."
version: "1.0.1"
author: "橙果数航"
---

# 橙果数航 海外游戏竞品投放对比

本 Skill 让助手用自然语言完成多款游戏的买量规模横向对比。用户只需说明要比哪几款游戏、什么时间范围；首次使用需本人在浏览器登录橙果数航（DataVoyage）并授权。助手负责执行脚本和整理结果。通过内置脚本直接访问橙果数航 MCP HTTP 服务，不依赖 WorkBuddy 连接器审核或安装。

## 必须遵守

- 必须使用本包脚本；禁止读取 WorkBuddy 或其他客户端的私有凭据缓存，禁止索取账号密码。
- 用户仅在官方浏览器页面登录。不得输出令牌、授权回调、缓存内容或完整授权 URL 到报告。
- 对比对象限定 2–5 款游戏。少于 2 款请用户补充；多于 5 款请用户选定本次比较对象，不擅自拆成不可直接比较的批次。
- 所有对比对象必须使用同一日期范围和同一筛选口径。禁止把各游戏不同范围的指标拼成一张对比表。
- 必须把去重素材、广告计划、复投素材与生命周期预估曝光分开呈现，不合并为单一“投放量”。
- 禁止把投放规模更大说成效率更高、收入更多或 ROI 更好；本技能不提供收入与 ROI 数据。
- 只执行用户请求所需的查询，不自动扩大游戏数量、国家范围或日期，不为诊断反复重试。

## 适用范围与环境

适用于“这几款游戏谁投得更猛”“素材量 / 广告计划对比”“谁的复投力度更大”这类横向量级比较。不适用于单款游戏的投放概况、素材明细检索、商店榜单查询，以及收入或 ROI 评估。

适用于 WorkBuddy 市场安装本技能后的使用：命令均相对于本 Skill 根目录，助手应自行定位安装目录，不依赖固定用户名或磁盘路径。

需要 Python 3.9+ 和 curl 7.70+。脚本只用 Python 标准库，无 pip 包、Node.js、ffmpeg 或 ffprobe 依赖。Windows 优先 `py -3`（没有时检测可用的 `python`）；macOS 使用 `python3`。缺少依赖时说明具体缺项，取得用户同意再安装，不要求新手配置 API Key、环境变量或连接器。

## 工作流程

1. 识别 2–5 款目标游戏与日期范围。游戏名称用 `search_games` 定位，Android 包名或 iOS 数字 ID 用 `resolve_game_by_identifier` 定位；同名候选不明确时请用户确认，禁止猜测或自行改写游戏令牌。`compare_games` 的 `game_ids` 数组元素必须是 `search_games` / `resolve_game_by_identifier` 返回的 `game_token` 原样字符串（形如 `X_SglHxBJwU=`），不是数字 ID。缺少会改变结果的条件时一次问清；参数含义与现成示例见[查询指引](references/query-guide.md)。
2. 直接运行正式入口完成查询。脚本会自动完成工具发现、身份校验和参数核对，**不需要先单独执行 --catalog**（该模式仅用于诊断）。查询参数以内联 JSON 传入：

   Windows：`py -3 scripts/comparison.py --tool compare_games --args "{\"game_ids\":[\"X_SglHxBJwU=\",\"gF7XbKteHtk=\"],\"date_from\":\"2026-08-26\",\"date_to\":\"2026-09-24\",\"rank_by\":\"material_count\"}"`

   macOS：`python3 scripts/comparison.py --tool compare_games --args '{"game_ids":["X_SglHxBJwU=","gF7XbKteHtk="],"date_from":"2026-08-26","date_to":"2026-09-24","rank_by":"material_count"}'`

   参数较多或含特殊字符时，可把参数写为 UTF-8 JSON 文件后用 `--args-file query.json` 代替 `--args`；文件只含查询条件，不含凭据。先执行一次 `get_context` 获取服务当前日期，再据此换算“近 30 天”等相对时间。参数必须匹配实时 schema，脚本会拒绝缺失必填项和未知参数。
3. 仅遇到 `LOGIN_REQUIRED` 或身份验证失败时运行 `py -3 scripts/auth.py login`（macOS 用 `python3`），告诉用户“请在打开的浏览器登录橙果数航并授权，完成后我会继续查询”。登录进程最多等待 10 分钟：使用后台任务或足够长的执行窗口，保持进程存活。用户关闭或拒绝后停止，不反复打开浏览器。成功出现 `LOGIN_OK` 后用原参数重新执行入口命令。
4. 脚本在查询前打印结果路径并生成 `.attempt` 标记；超时或中断后先检查该路径。存在 result 文件就读取复用；只有标记没有结果时，说明结果未确认，不自动重试可能已计费的请求。输出路径已存在时按 `OUTPUT_EXISTS` 提示读取已保存结果，不重跑。
5. 读取脚本打印的 `output` 文件，先检查业务错误（`error_code`）、提示、实际日期及筛选条件，再按[结果呈现](references/output-format.md)组织答案。失败或中断时按[排障与续查](references/troubleshooting.md)处理。

使用助手支持的长任务或后台进程机制定期查看进度，不能因单次工具等待上限结束就重启查询；网络、代理和服务器也可能提前超时，不承诺固定总耗时。

## 授权与失败处理

同一系统用户的本包与橙果数航其他技能包（素材查询、图搜视频、商店榜单、素材相似与复用）共用自有授权存储，已有有效授权可复用；不读取连接器登录状态。已有 MCP 授权不等于本包获得授权。缓存保存在系统用户应用数据目录，脚本限制本地访问权限，不要读取或展示缓存。已有 `AUTH_TOKEN` 环境变量时脚本优先使用它，但新手无需设置。

401 或登录失效时引导重新授权；403 或额度不足时解释账号权限问题并停止；网络错误时保留结果路径，检查用户网络后再决定是否重试，不自动更改代理或关闭证书验证。脚本默认直连官方服务，企业网络只允许代理时需由用户确认网络策略。工具缺失时说明账号或服务尚未提供能力，不猜测接口。

用户明确要求退出时执行 `py -3 scripts/auth.py logout`（macOS 用 `python3`）。这会撤销并删除共享授权，其他橙果数航技能包也需要重新登录；不会清除其他连接器缓存，也不会修改环境变量。

## 输出与验收

先说明对比的游戏、实际日期范围、国家筛选和排序口径（`rank_by`），再用表格逐行列出每款游戏的去重素材数、广告计划数、复投素材数与生命周期预估曝光，并突出与用户问题相关的差异。计算倍数时分母必须非零且口径一致；零值或缺失不能据此计算增长率。

国家条件只表示投放目标国家列表包含该国家，不代表当地曝光或用户偏好；生命周期曝光是累计估算，不是所选日期的新增曝光，也不等于实际花费、转化或 ROI。

验收必须满足：所有对象同期同口径；四类指标分列不混同；某款游戏取不到数据时标注缺失，不以零替代，也不擅自替换游戏；不把规模更大说成效率更高。完整回答本次横向比较即完成，不扩展成长篇策略报告。
