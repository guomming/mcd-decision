# WorkBuddy 开发上下文

本文件记录本项目在腾讯 WorkBuddy 中的实际开发对话过程，用于核验 WorkBuddy 专项奖励条件。
开发时间：2026-10-10 ~ 2026-10-11
开发环境：WorkBuddy（Windows），麦当劳 MCP 以自定义连接器方式挂载

---

## 一、需求起点

**用户**：（发来微信公众号文章链接）
https://mp.weixin.qq.com/s/-6lOK0oh3hoM-mj7YbiAog

**用户**：查看下这篇文章，看下我需要做什么才可以的

**WorkBuddy**：抓取文章后发现这只是引子，主动去 GitHub 找到官方仓库
`M-China/mcd-developer-innovation-challenge` 与 `M-China/mcd-mcp-server`，
完整拉取了活动规则、报名条件、仓库必需文件清单、MCP 工具列表、奖励设置与排行榜快照，
输出《参赛行动清单.md》，并画出五步流程图。

结论要点：排名只看 GitHub 公开 Star 数；仓库必须含 README.md、CONTEST_DECLARATION.md
（原文不可改）、MCP_INTEGRATION.md、mcp-config.example.json、workbuddy.md、源代码。

---

## 二、验证 MCP 连通性

**用户**：帮我看看附近有什么麦当劳门店

**WorkBuddy**：
1. 加载 `query-nearby-stores` / `delivery-query-addresses` 工具 schema
2. 调用 `delivery-query-addresses` → 返回 `addresses: []`，判定账号无已存地址
3. 因工具需位置入参，向用户提问：所在城市 + 取餐方式
4. **用户回答**：广东东莞 / 到店自取
5. 调用 `query-nearby-stores`，入参
   `{"beType":"1","city":"东莞","keyword":"东莞","searchType":"2"}`
6. 成功返回 5 家门店，最近一家 254 米且 24 小时营业

> 这一步实测暴露了两个原本文档里没写的关键约束：
> `beType` 与 `searchType` 为必填；`delivery-query-addresses` 返回空是常态。
> 两点都已补进 SKILL.md 的「关键接口的必填参数」与「失败处理」章节。

---

## 三、同步 ima 知识库并复用既有 Skill 配置

**用户**：请先读取 ima 知识库项目文件夹中「麦当劳 × WorkBuddy 创意开发」项目的全部内容，
包括其中的思考过程文档，并与 ima 知识库中的数据保持同步……检查该项目内我已创建的 skill 配置，
评估其是否能直接复用……

**WorkBuddy**：
1. `search_knowledge_base` 搜「麦当劳」无结果 → 换「WorkBuddy」「创意开发」→ 最终用
   `get_knowledge_base_list(type=KBT_MINE_KB)` 定位到知识库「项目」（id 7513784725807549）
2. `search_knowledge(query=麦当劳)` 命中文件夹
   `folder_7515002562946852`「麦当劳 × WorkBuddy 创意开发」，含 4 个文件
3. `get_knowledge_list(folder_id=...)` 确认目录完整（total_size=4）
4. `fetch_media_content` 逐个拉取 4 份全文：
   - 麦当劳创意开发_产品思路与Skill骨架（5903 字节）
   - SKILL（8446 字节）
   - README（2537 字节）
   - 配套源码与配置（4294 字节）
5. 全部落盘到 `_ima同步/`，保持与 ima 一致
6. 对照官方参赛规则逐项体检，发现 3 个阻断性缺口（CONTEST_DECLARATION.md /
   MCP_INTEGRATION.md / workbuddy.md 缺失）与 4 处需修正项
7. 产出修正后的完整 `mcd-decision/` 目录

---

## 四、在 WorkBuddy 中做的具体工作

- 获取并解读官方赛事规则（GitHub 双仓库）
- 通过 MCP 连接器实际调用麦当劳工具并验证返回结果
- 读取 ima 知识库 4 份文档并落地到工作区
- 重写 SKILL.md 的 frontmatter 为合规的 7 字段格式
- 补齐 SKILL.md 中缺失的必填参数与失败处理
- 新建 MCP_INTEGRATION.md（含调用流程图与业务价值）
- 新建 CONTEST_DECLARATION.md（官方原文，一字未改）
- 新建 mcp-config.example.json（改为环境变量占位符）
- 新建 README.md、.gitignore、workbuddy.md
- 修正「套餐不支持更换」这一过时结论（MCP v1.0.5 起已支持）
- 修正工具数量：ima 记录的 18 个 → 官方实际 30+ 个

---

## 五、结论

本项目从需求调研、规则解读、MCP 连通性验证、知识库同步到 Skill 重写与参赛文件补齐，
全程在 WorkBuddy 中完成，麦当劳 MCP 亦通过 WorkBuddy 的自定义连接器挂载并实际调用成功。
