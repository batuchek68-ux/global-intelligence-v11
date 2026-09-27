# 尽调智能体契约

## 当前状态

合规/制裁筛查与交易对手身份核验已注册到 v12 编排任务图。当前尚未注册 OFAC、UN、EU、UK 的生产名单下载适配器，也没有已验收的哈萨克斯坦、印度尼西亚或乌兹别克斯坦官方企业登记适配器。因此：

- 有名称但无完整名单数据时返回 `inconclusive`，不表示未命中。
- 没有官方企业登记适配器时返回 `unavailable`，不表示身份已核验。
- 风险门禁会把这些未决状态升级为人工审查；不得据此自动报价、签约、付款、承诺或对外发布。
- 普通网页搜索结果不是名单源或官方企业登记证明。

## 运行方式

本地运行时从仓库根安装依赖，在 `backend/` 下调用共享入口：

```powershell
python -m pip install -r requirements.txt
python backend/workflows/run_due_diligence.py --input path/to/request.json
```

Windows 桌面入口：双击桌面上的 **Global Intelligence - 尽调核验** 图标，按提示填写事项、法定名称和国家/地区，别名及注册号可留空。仓库中的 `run_due_diligence_desktop.ps1` 是启动器；更换仓库位置后需重新创建快捷方式并将其指向新位置。

`request.json` 使用下方的 v12 请求结构。GitHub Actions 中手动运行 **Due Diligence Review**，将同一 JSON 对象作为 `request_json` 输入。可选配置 `BING_SEARCH_KEY` 和 `BRAVE_SEARCH_API_KEY` 来支持一般网页研究；这些搜索源不等同于制裁名单或官方企业登记源。

单次完整结果保存在 `backend/reports/due_diligence/`，GitHub workflow 会将 JSON/Markdown 上传为保留 30 天的 artifact。报告含查询与交易对手信息，应按敏感业务资料管理；不要把报告提交到仓库。

每次成功运行会把不含查询、主体名称、别名或注册号的状态记录追加至 `memory/due_diligence_runs.jsonl`，并更新 `memory/due_diligence_learning.json` 中的累计状态、来源可用性和基于观察生成的改进建议。Actions 会只提交这两份匿名记忆文件。学习过程仅调整建议，不会自动改业务规则、名单适配器或源代码。

仓库已有的 **Codex Autonomous Repair** workflow 独立负责受限的 Python 编译修复、测试验证和回滚；它不会擅自修改业务逻辑。两条 workflow 的职责不同：尽调 workflow 执行业务分析并积累匿名运行记忆，自动修复 workflow 检查和修复限定范围内的语法问题。

## v12 请求输入

现有 `POST /v1/query` 路由保持不变。调用方可以在已有 `metadata` 对象中提供主体；不提供时旧客户端行为保持兼容。

```json
{
  "query": "Review cross-border transaction",
  "metadata": {
    "counterparties": [
      {
        "name": "Example Trading LLC",
        "aliases": ["Example Trading"],
        "country": "Kazakhstan",
        "registration_number": "optional"
      }
    ],
    "sanctions_screening_required": true
  }
}
```

主体名称会同时触发两项检查。显式 `sanctions_screening_required` 或抽取到风险词时，即使没有提供主体，也会触发筛查并返回 `inconclusive`。

## 智能体契约

| 智能体 | 调用条件 | 结果状态 | 放行边界 |
| --- | --- | --- | --- |
| `sanctions_screening` | 有主体，或明确请求筛查/识别到相关风险 | `potential_match`、`no_match_found`、`inconclusive`、`skipped` | `no_match_found` 要求四类名单来源均有效：辖区官方域名、可解析名单更新时间、最近 24 小时的 UTC 抓取时间、非空且结构正确的记录。命中或不确定必须人工复核。 |
| `counterparty_verification` | 请求中提供命名主体 | `verified`、`partial`、`conflicting`、`unavailable`、`skipped` | `verified` 要求官方适配器提供法定名称、国家、注册号、来源标识、HTTPS 来源和 24 小时内查询时间，且提交名称/别名或注册号与登记结果相符。身份核验不等于信用或履约能力核验。 |

名单匹配目前仅执行 Unicode 规范化后的精确名称/别名比较，不执行模糊匹配、跨文字转写、受益所有权或控制关系分析。`no_match_found` 只表示这些名单在记录时间点未找到精确名称匹配，不是法律清白结论。

## 适配器接入门槛

名单适配器通过 `register_sanctions_source(jurisdiction, provider)` 注册，辖区只允许 `OFAC`、`UN`、`EU`、`UK`。provider 返回 `status: available`、非空的结构化 `records`、官方 HTTPS `source_url`、名单 `updated_at` 日期和抓取时间 `checked_at`。来源域名还必须符合辖区白名单。

企业登记适配器通过 `register_counterparty_registry(country, provider)` 注册。provider 必须只查询所声明司法辖区的官方登记，并返回真实法定名称、国家、注册号、来源标识、HTTPS 来源和 UTC 查询时间。接入前应核实官方域名、自动化访问条款、查询限制、数据保护要求和更新时间语义。

优先核验的官方入口：

- OFAC Sanctions List Service: https://ofac.treasury.gov/sanctions-list-service
- UN Security Council Consolidated List: https://main.un.org/securitycouncil/en/content/un-sc-consolidated-list
- EU Consolidated Financial Sanctions List: https://data.europa.eu/data/datasets/consolidated-list-of-persons-groups-and-entities-subject-to-eu-financial-sanctions
- UK Sanctions List: https://www.gov.uk/government/publications/the-uk-sanctions-list
- Kazakhstan eGov business services: https://egov.kz/cms/en/services/business_registration
- Indonesia OSS: https://oss.go.id/
- Uzbekistan public services portal: https://my.gov.uz/en

这些入口链接本身不代表自动化数据接口已经验证或接通。接入每个适配器前需要用官方样本验证解析、更新检查、失败降级及误匹配案例。

## 回归验收

- 旧请求不带 `metadata.counterparties` 时 v12 路由和响应仍可用，两名尽调智能体返回 `skipped`。
- 任一名单来源缺失、不可达、过期、非官方域名或结构异常时，筛查不得返回 `no_match_found`。
- 精确名称/别名命中返回 `potential_match`，而不是自动判定受制裁。
- 登记主体名称、国家或已提供注册号冲突时返回 `conflicting`。
- 名单筛查未决或主体核验不可用/不完整/冲突时，风险门禁要求人工审查。
- 最终输出保留每个智能体的状态、证据来源与限制。