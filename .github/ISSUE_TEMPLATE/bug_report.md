---
name: Bug report
about: 报告 Skill 报错、登录授权异常、查询结果异常等问题
title: "[bug] "
labels: bug
assignees: ""
---

## 现象

<一句话说明>

## 期望

<应该出现什么>

## 复现步骤

1. 调用的脚本: `py -3 scripts/<name>.py --tool <tool>`
2. 参数(脱敏,不要带 token):
   ```json
   { }
   ```
3. 时间: `YYYY-MM-DD HH:MM UTC`
4. 网关: `https://mcpapi.datavoyage.cn/mcp` (或自定义)

## 实际看到

- `error_code`(如有):
- 响应片段(脱敏):
  ```
  ...
  ```

## 环境

- 客户端: Claude / Codex / Cursor / 其他(版本)
- 系统: Windows 10/11 / macOS / Linux
- Python: 3.9 / 3.10 / 3.11 / 3.12 / 3.13
- curl: `curl --version` 输出的前 3 行

## 备注

其它补充。如果错误是数据本身(广告不存在/字段缺失),请附上游戏名/广告链接/查询日期。
