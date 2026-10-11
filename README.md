# 选择困难症救星 · McDecision

2026 麦当劳 × WorkBuddy 程序员创意开发大赛参赛作品
基于麦当劳中国官方 MCP，用三种饮食人格帮用户决定"今天吃啥"。

## 一句话

别人做的是"工具壳"，我做的是"决策器"。决策器的心，是可解释的决策规则。

## 为什么是它

麦当劳 MCP 提供了 30+ 个取数与交易工具，但**没有任何一个"推荐"接口**。
大多数作品把这些工具包一层壳，做的仍是"查菜单 / 算价格"。
真正的痛点其实在更前面一步：**每天中午站在点单页前，不知道吃什么。**

所以本项目不拼工具覆盖度，而是把模糊的心理状态翻译成可计算的权重与约束，
做到三件事：决策可解释、约束前置、越用越懂你。

## 三个入口

| | | |
|---|---|---|
| 🎲 看心情 | 交给命运的佛系我 | 加权随机（偏好 + 时段 + 不重复 + 活动），不是纯抽 |
| 💰 薅一把 | 精打细算的我 | 一键领券 + 预算内组合试算 → 性价比 Top3 + "这单值不值" |
| 😋 宠自己 | 今天想犒劳的我 | 偏好匹配度排序 + 馋点理由，价格无所谓 |

## 快速开始

### 1. 拿 MCP Token

- 打开 https://open.mcd.cn/mcp
- 用麦当劳账号（手机验证码）登录
- 点右上角「控制台」→「激活」→ 复制 Token

### 2. 挂载 MCP

把 `mcp-config.example.json` 复制为 `mcp-config.json`，把 `${MCD_MCP_TOKEN}` 换成真实 Token，
在 WorkBuddy 左侧边栏【专家·技能·连接器】→【连接器】→【自定义连接器】→【配置MCP】中粘贴并启用。

```bash
# 仅在使用脚本路径时需要
export MCD_MCP_TOKEN="你的token"
```

### 3. 装上 Skill

把整个 `mcd-decision/` 目录放到 WorkBuddy 技能目录（如 `~/.workbuddy/skills/mcd-decision/`）。

### 4. 跑起来

```bash
# 看有哪些工具
python3 scripts/mcd_client.py tools/list

# 查当前时间（判时段）
python3 scripts/mcd_client.py now-time-info '{}'

# 查附近门店（四个参数都不能省）
python3 scripts/mcd_client.py query-nearby-stores '{"beType":1,"searchType":2,"city":"东莞","keyword":"东莞"}'

# 查菜单
python3 scripts/mcd_client.py query-meals '{"storeCode":"xxx"}'

# 一键领券
python3 scripts/mcd_client.py auto-bind-coupons '{}'
```

### 5. 自然语言触发

- "麦当劳今天吃啥"
- "薅一把，30 块怎么点最省"
- "宠自己，想吃好的"
- "中午不知道吃什么"

## 目录结构

```
mcd-decision/
├── SKILL.md                  # 技能主文件（Agent 运行时加载）
├── README.md                 # 本文件
├── MCP_INTEGRATION.md        # MCP 接入说明（参赛必需）
├── CONTEST_DECLARATION.md    # 参赛声明（参赛必需，内容不可改）
├── mcp-config.example.json   # MCP 挂载配置示例（脱敏，仅占位符）
├── workbuddy.md              # WorkBuddy 开发上下文（专项奖励凭证）
├── .gitignore                # 排除本地敏感文件
└── scripts/
    └── mcd_client.py         # MCP 通用客户端（仅标准库）
```

## 设计原则

> 取数交给 MCP，算术交给代码，表达交给 Agent，决策规则交给我自己。

- **取数**：全部走麦当劳 MCP，不写爬虫。
- **算术**：金额一律由 `calculate-price` 产出（÷100），模型不口算。
- **表达**：Agent 负责把结果讲成人话。
- **决策**：三入口的权重 / 约束 / 匹配逻辑，是本作品真正的差异点。

## 已知限制

- 仅支持麦当劳中国（大陆，不含港澳台）。
- Token 限流 600 次/分钟，超限返回 429。
- 券的商品编码与菜单商品编码是两套体系，不可混用。
- 口味画像为本地文件，换设备不迁移。

## 安全与合规

- Token 只走环境变量，不入库、不外传、不打印、不提交。
- `mcp-config.json` 与 `preferences.json` 已列入 `.gitignore`。
- 口味画像仅存本地 `preferences.json`，不上传。
- 本项目为参赛作品，非麦当劳官方产品；餐品信息、价格及供应状态以麦当劳官方渠道实时结果为准。

## 免责

项目输出仅供参考，不构成医疗、营养或其他专业建议。
