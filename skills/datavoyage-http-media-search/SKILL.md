---
name: "datavoyage-http-media-search"
display_name: "橙果数航 海外游戏买量素材图搜视频 视频搜视频"
display_name_en: "DataVoyage Ad Video Search"
description: "上传图片或视频，搜索海外游戏（以手游为主）相似广告买量素材。支持图搜视频、以图搜视频、视频搜视频等多模态检索，帮助查找竞品广告与创意参考，返回关联游戏、相似度及素材链接。不用于纯关键词搜索。"
description_zh: "上传图片或视频，搜索海外游戏相似买量素材与竞品广告创意。支持图搜视频、以图搜视频、视频搜视频等多模态检索，返回关联游戏、相似度及素材链接。覆盖手游为主的出海游戏广告市场。"
description_en: "Upload an image or video to find similar mobile game ads in overseas markets. Discover competitor creatives and inspiration with related games, similarity scores and creative links."
version: "1.0.4"
author: "橙果数航"
---

# 橙果数航 海外游戏买量素材图搜视频 视频搜视频

本 Skill 让助手完成本地媒体检查、上传、等待处理和相似视频检索。用户只需提供文件和筛选要求；首次使用需本人在浏览器登录橙果数航（DataVoyage）并授权。适用于支持本地脚本的 WorkBuddy 等助手，不要求读取 MCP 客户端的私有凭据缓存。

## 必须遵守

- 只上传用户指定、授权搜索的文件。检索会消耗账号查询额度；不要为测试凭据创建额外票据或付费查询。
- 签票、状态、上传、搜索必须全程走本包 HTTP 脚本和同一账号，禁止混用 MCP 工具签发的票据。
- 不将 AUTH_TOKEN、OAuth 缓存、media_token、完整授权 URL 写入聊天、日志或共享报告；禁止索取用户账号密码。
- 不删除其他 MCP 服务凭据，不自动换账号，不擅自改变代理、关闭 TLS 验证或安装软件。
- 上传失败、中断或超时先续查原任务；禁止循环签票、反复上传或改变查询条件。更换条件可能产生新的计费。

## 适用范围与环境

在 WorkBuddy 市场安装本技能后，使用技能安装目录内的 scripts 和 references。手动升级时替换整个技能目录，不混用旧脚本。当前目录中的命令均相对于本 Skill 根目录，助手应自行定位，不依赖固定用户名或磁盘。

需要 Python 3.10+、curl 7.70+。ffprobe（FFmpeg 附带）是可选的本地视频检查工具，不要求用户安装；图片完全不使用它。脚本只用 Python 标准库，无 pip 依赖。

Windows 使用 `py -3`（没有时检测可用的 `python`）；macOS 使用 `python3`。curl 自动定位；Windows 优先系统 curl，macOS 支持系统或 Homebrew curl。缺少依赖时说明缺什么，按用户允许的方式安装，随后重试本地检查。

## 工作流程

1. 确认文件和用户要求。默认 10 条，可选 1–50；日期必须同时提供 `--date-from YYYY-MM-DD --date-to YYYY-MM-DD`，跨度最多 180 天。不指定时使用服务默认范围，并在结果中报告实际 scope。
2. 直接运行搜索入口，不要例行先执行 --check-only、auth.py status 或测试脚本。正式入口已经完成本地检查和身份验证，重复预检查只增加等待：

   Windows：`py -3 scripts/run_local.py --file "用户文件路径" --limit 10`

   macOS：`python3 scripts/run_local.py --file "用户文件路径" --limit 10`

   默认生成私有任务目录，助手记录输出中的 work_dir，不需要用户选择目录。已有会话可继续使用，脚本按需刷新令牌，不必每次登录。全流程为检查文件 ↓ 验证身份 ↓ HTTP 签票 ↓ 状态核验 ↓ 中转上传 ↓ 等待搜索结果。
3. 仅遇到 LOGIN_REQUIRED 或身份验证失败时，按[排障与续查](references/troubleshooting.md)处理授权。首次无授权时运行 `python3 scripts/auth.py login`（Windows 替换为 `py -3`），告知用户在浏览器登录并授权，保持进程运行，最长等 10 分钟。不要自动反复登录。已有 MCP 授权不等于脚本获得授权，本包目前独立授权；已安全配置的 AUTH_TOKEN 优先使用，不要展示其值。

   登录完成后检查原 work_dir：存在 private-task.json 时执行 --resume；存在 attempt.json 但没有 private-task.json 时停止排查，不能盲目签票；两者都不存在时，可按原参数重新执行并指定原 --work-dir，不会重复已有任务。
4. 使用助手支持的长任务/后台进程机制，定期查看进度，不能因单次工具等待 120 秒结束就重启上传。Windows 自行启动后台进程时隐藏窗口。上传最多等待 600 秒，处理轮询每次运行最多 300 秒；网络、代理和服务器也可能提前超时，不承诺固定总耗时。
5. 成功后读取 result.json，按[结果呈现](references/output-format.md)交付。失败时读取脱敏 diagnostic.json，按[排障与续查](references/troubleshooting.md)处理。用户只需要提供文件、必要的搜索要求，并在首次授权时操作浏览器；路径管理、参数和诊断由助手处理。

文件检查自动执行：JPEG/PNG/WebP 图片最多 10 MiB；MP4/MOV/WebM 视频最多 50 MiB、120 秒。服务端负责最终有效性检查。有 ffprobe 时本地检查时长和视频流；没有时正常继续上传，video_validation=deferred_to_server、duration_seconds=null 表示本地尚未验证时长。禁止为此要求安装 FFmpeg。已有 ffprobe 检测失败或视频超限时仍停止报告。

按需加载参考资料：结果呈现使用 @references/output-format.md；失败或中断时使用 @references/troubleshooting.md。

## 续查与清理

续查命令：`python3 scripts/run_local.py --resume --work-dir "上次输出的任务目录"`。只使用原文件和保存的原查询；不添加 limit、日期或 file 参数。已有结果直接返回本地结果；没有结果时核验同一任务，再继续查询，不新建票据。服务端过期或失败则停止并说明。

用户确认不再续查后，可以执行 `python3 scripts/run_local.py --cleanup --work-dir "任务目录"`，仅删除该任务的 private-task.json，保留结果与诊断；不删除服务端媒体。退出本包授权用 `python3 scripts/auth.py logout`，撤销并删除本包保存的授权；不会删除其他应用凭据，也不会清除外部设置的 AUTH_TOKEN。

授权存储在当前操作系统用户的 DataVoyage/media-search 私有目录；任务默认也存这里。macOS 限制目录/文件权限，Windows 设置当前用户 ACL。不要把整个任务目录发给别人，只分享需要的结果和脱敏诊断。

## 验收

依赖检查通过、登录状态有效、上传返回成功、搜索返回 items 才算全流程完成；空 items 是有效的零结果，不能编造相似素材。processing 只表示处理中，不能宣称成功。日常搜索不运行维护测试，不要求用户逐项验收。发生问题时按[使用问题处理](references/troubleshooting.md)操作。
