---
name: 登录授权问题
about: auth.py login 失败、token 失效、登录后查询仍报 LOGIN_REQUIRED
title: "[auth] "
labels: auth
assignees: ""
---

## 触发操作

<具体跑了什么命令,例如 `py -3 scripts/auth.py login`>

## 期望

<成功登录,出现 `LOGIN_OK` 标记,后续查询不再报 LOGIN_REQUIRED>

## 实际看到

- 浏览器是否自动打开? (是/否)
- 是否停在"等待浏览器登录"页? (是/否,等了多久)
- 错误输出(脱敏,不要带 token):
  ```
  ...
  ```
- 系统用户应用数据目录里有没有产生缓存文件? (不要贴路径或内容,只说"有/无"或大小变化)

## 尝试过

- [ ] 关闭浏览器所有 datavoyage 标签页后重试
- [ ] 重新运行 `py -3 scripts/auth.py logout` 再 `login`
- [ ] 切换默认浏览器
- [ ] 检查企业代理是否拦截了 OAuth 回调(localhost 或 127.0.0.1)

## 环境

- 系统: Windows / macOS / Linux
- 浏览器: Chrome / Edge / Safari / Firefox(版本)
- 是否企业网络/代理: 是 / 否
