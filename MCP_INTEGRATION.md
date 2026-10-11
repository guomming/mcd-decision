# MCP 接入说明

本文件说明本项目实际使用的麦当劳中国 MCP Server、调用的 Tool、完整调用流程，以及由此产生的业务价值。

## 1. 使用的 MCP Server

| 项目 | 值 |
|---|---|
| 官方名称 | 麦当劳中国 MCP Server |
| 接入地址 | `https://mcp.mcd.cn` |
| 传输协议 | Streamable HTTP |
| 认证方式 | HTTP Header `Authorization: Bearer <Token>` |
| Token 申请入口 | https://open.mcd.cn/mcp（登录麦当劳账号 → 控制台 → 激活） |
| 官方文档 | https://github.com/M-China/mcd-mcp-server |
| 限流 | 600 次/分钟（超限返回 429） |
| 当前版本 | v1.0.9（2026-09-10） |

配置文件见 `mcp-config.example.json`，其中 Token 以 `${MCD_MCP_TOKEN}` 环境变量占位符表示，**仓库内不含任何真实凭证**。

## 2. 实际调用的 Tool 清单

本项目按"取数 → 决策 → 算价 → 下单"四段使用 MCP，共调用以下工具：

### 取数层

| Tool | 在项目中的作用 |
|---|---|
| `now-time-info` | 获取当前时间，据此判定早餐/午餐/下午茶/夜市/宵夜时段，作为看心情模式的权重输入 |
| `query-nearby-stores` | 到店场景拿候选门店（含营业时间、是否支持预约、预约时段选项） |
| `delivery-query-addresses` | 外送场景取用户已有配送地址 |
| `delivery-create-address` | 地址为空时引导新建 |
| `delivery-query-stores` | 取该地址的可配送门店 |
| `query-meals` | 拉门店在售菜单，作为决策候选集 |
| `list-nutrition-foods` | 补营养数据，供用户设置健康约束时过滤 |
| `query-meal-detail` | 看套餐组成与可替换项，避免拼错参数 |
| `campaign-calendar` | 查当月活动，给"当季新品/活动中商品"加权 |

### 决策层（本项目核心，不依赖 MCP）

MCP **不提供任何"推荐"接口**。三种饮食人格的权重规则、约束前置逻辑、性价比判定与可解释理由生成，全部由本 Skill 自己实现（详见 `SKILL.md` 第 5 节）。这构成了本作品与"工具壳"类作品的核心差异。

### 算价层

| Tool | 在项目中的作用 |
|---|---|
| `available-coupons` | 查麦麦省当前可领券 |
| `auto-bind-coupons` | 一键领取全部可领券 |
| `query-store-coupons` | 查指定门店可用券 |
| `query-my-coupons` | 查我的券包 |
| `calculate-price` | **唯一的价格来源**，产出原价/券后/实付/优惠金额 |

所有金额一律取 `calculate-price` 返回值并 ÷ 100（接口单位为分），模型不做任何口算。

### 下单层

| Tool | 在项目中的作用 |
|---|---|
| `create-order` | 用户确认后下单，返回订单详情与支付链接 |
| `query-order` | 查订单状态 |
| `order-list` | 读历史订单，避免重复推荐最近点过的餐品 |
| `cancel-order` | 用户要求取消时使用 |

### 扩展能力（已接入但 v1 未在主流程启用）

`query-my-account`、`mall-points-products`、`mall-product-detail`、`mall-create-order`、`mall-order-list`、`mall-order-detail`、`query-lottery-info`、`draw-lottery`、`query-my-prizes`、`query-party-city`、`query-party-store`、`query-partystore-date`、`query-partystore-session`、`party-order-create`、`query-meal-assistance`。

## 3. 调用流程

```
用户输入（一句话状态）
   │
   ├─ 识别人格：看心情 / 薅一把 / 宠自己
   └─ 收集约束：预算、人数、忌口、时段、到店 or 外送
        │
        ▼
  【1】now-time-info                    → 判定时段
  【2】query-nearby-stores              → 拿门店（beType + searchType + city + keyword）
      或 delivery-query-addresses
         → delivery-create-address（空时）
         → delivery-query-stores
        │
        ▼
  【3】query-meals                      → 候选集
      （健康约束时）list-nutrition-foods
      （加权时）campaign-calendar
        │
        ▼
  【4】available-coupons → auto-bind-coupons   （薅一把必做）
        │
        ▼
  【5】★本 Skill 决策引擎★
       看心情 → 加权轮盘（偏好 +3 / 时段 +2 / 不重复 +1 / 活动 +1）
       薅一把 → 预算内组合枚举，性价比 Top3 + "这单值不值"判断
       宠自己 → 偏好匹配度排序 + 馋点理由
        │
        ▼
  【6】calculate-price                  → 唯一价格来源（÷100）
        │
        ▼
  【7】输出卡片（主推 1 + 备选 2 + 理由 + 省钱明细）
        │
        ▼
     用户确认 → create-order → query-order
```

设计原则：**取数交给 MCP，算术交给代码，表达交给 Agent，决策规则交给本 Skill。**

## 4. 业务价值

1. **把"不知道吃啥"变成一次可解释的决策。** MCP 提供的是数据与交易能力，不提供偏好判断。本 Skill 用三种饮食人格把模糊的心理状态翻译成可计算的权重与约束，直接消解选择困难。
2. **决策可解释，而不是黑箱推荐。** 每条推荐都给出理由（"晚饭点，你上次选了鸡块，这次换同价位板烧"），用户信任度高于单纯排序。
3. **约束前置，减少返工。** 预算/忌口/时段在推荐前就约束，而不是先列一堆再筛，交互轮次显著下降。
4. **省钱可核对。** 金额一律来自 `calculate-price`，并说清省在哪个券、凑了什么单，避免"看起来省了实际没省"。
5. **越用越准。** 本地口味画像沉淀，权重随使用演化，形成 MCP 本身不具备的长期价值。

## 5. 敏感信息处理

- Token 仅通过环境变量 `MCD_MCP_TOKEN` 注入，仓库内只保留 `${MCD_MCP_TOKEN}` 占位符。
- `preferences.json`（口味画像）与 `mcp-config.json`（真实配置）已列入 `.gitignore`，不进公开仓库。
- 不在任何文档、截图、日志中打印真实 Token、手机号或收货地址。
