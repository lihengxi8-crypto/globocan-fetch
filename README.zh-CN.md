# globocan-fetch v1.1.0

一个面向研究者的 [GLOBOCAN Cancer Today](https://gco.iarc.who.int/today/) 数据下载与学习工具。

`globocan-fetch` 用于可复现地获取、记录、理解和分析 GLOBOCAN **发病与死亡表格估计数据**，支持 CSV 和 Parquet 输出。

[English](README.md)

> **项目状态：v1.1.0。**
> `globocan-fetch` 不是 IARC、WHO 或 GCO 官方工具。本项目使用的是从公开 Cancer Today 网页应用中观察到的请求路径，不应将其视为由官方承诺长期稳定的公共 API。本仓库仅包含代码，不分发下载得到的 GLOBOCAN 数据。

---

<!-- section: what-is-globocan -->
## 1. 什么是 GLOBOCAN？

GLOBOCAN 是国际癌症研究机构（IARC）Global Cancer Observatory 的重要组成部分。Cancer Today 提供不同国家及其他人群分组的癌症负担估计。

第一次使用时最需要理解的是：

**GLOBOCAN 是估计数据（estimates）。**

它不是：

- 患者级数据库；
- 个体医疗记录集合；
- 各国癌症登记病例的原始全量导出；
- 癌症登记微观数据的替代品。

例如，字段 `total` 表示在指定人群、性别、癌种和年龄范围下的**估计新发病例数或死亡数**。

GLOBOCAN 的**数据年份**与实际访问或下载数据的日期并不是同一个概念。同一个数据年份也可能存在后续发布或更新日期。

在本文档撰写时，Cancer Today 页面显示的版本为：

**GLOBOCAN 2024 – 08.07.2026**

正式研究中仍应以使用数据时 Cancer Today 官网显示的信息为准。

为了保证研究可复现，建议至少记录：

- GLOBOCAN 数据年份；
- 官网提供的版本或发布日期信息（如有）；
- 数据访问/下载日期；
- 癌种定义；
- 性别；
- 年龄范围；
- 指标；
- 分析代码；
- `globocan-fetch` 生成的 manifest。

---

<!-- section: what-is-globocan-fetch -->
## 2. globocan-fetch 是什么？

`globocan-fetch` 是一个用于可复现获取 Cancer Today 表格估计数据的小型命令行工具。

它适合以下场景：

- 同一批 GLOBOCAN 查询需要反复运行；
- 需要完整记录查询条件；
- 希望直接使用 Python、R、Stata、DuckDB 等工具分析下载结果；
- 希望保留一个可以追溯和复现的数据快照。

本工具可以：

- 按指标、性别、癌种/site 和年龄范围查询数据；
- 当前使用 `populations=all`，因此一次查询可以同时返回国家和 GCO 聚合人群；
- 下载并缓存人群和癌种元数据；
- 为结果补充可读的人群名称、ISO3、癌种名称等信息；
- 使用保守的全局请求速率限制；
- 对临时网络错误进行重试；
- 输出 CSV 或 Parquet；
- 维护可断点续传的 `manifest.json`；
- 记录输出文件和元数据的哈希；
- 自动生成双语 `DATA_DICTIONARY.md`。

Cancer Today 官方网站仍然是以下信息的权威来源：

- 可视化浏览数据；
- 查看当前官方展示方式和术语；
- 核对当前 GLOBOCAN 发布版本；
- 阅读 IARC/GCO 最新数据使用条款。

`globocan-fetch` **不是一个新的癌症数据库**，也不会改变 GLOBOCAN 的估计值。

---

<!-- section: supported-data -->
## 3. 支持哪些数据？

### 指标

当前版本支持：

- `incidence`：发病
- `mortality`：死亡

Cancer Today 网页还存在其他视图和指标，但目前不属于 `globocan-fetch` 的支持范围。

### 性别

支持：

- `both`：两性合计
- `male`：男性
- `female`：女性

### 癌种/site 条目

癌种定义来自所查询年份的 Cancer Today metadata endpoint。

对于 GLOBOCAN 2024，目前观察到的元数据包含 **41 个 cancer/site entries**。

这并不意味着 GLOBOCAN 包含 41 个互相排斥的独立癌种。

其中还包括组合或汇总条目，例如：

- All cancers；
- All cancers excluding non-melanoma skin cancer；
- Colorectum；
- Other specified cancers；
- Unspecified sites。

因此不建议依赖人工维护的癌种列表，而应查看当前年份的运行时 metadata：

```bash
globocan-fetch cancers --year 2024
```

### 人群

一张返回表中可能同时包含：

- 单个国家；
- World；
- 大洲；
- UN 子区域；
- WHO 区域；
- HDI 分组；
- 世界银行收入分组；
- GICR hub；
- 其他 GCO 聚合人群。

因此：

**国家行和聚合人群行会同时存在于同一张输出表中。**

### 年龄范围

当前工具支持：

- 预定义累计年龄范围；
- 单独五岁年龄组。

五岁年龄组使用 `0`–`17` 的零起始索引。

---

<!-- section: quick-start -->
## 4. 快速开始

### 从 GitHub 安装

建议使用 Python 3.10 或以上版本。

目前 `globocan-fetch` 尚未通过 PyPI 发布，因此需要直接从 GitHub 仓库安装。

首先下载项目代码并进入项目目录：

```bash
git clone https://github.com/lihengxi8-crypto/globocan-fetch.git
cd globocan-fetch
```

然后创建独立的 Python 环境并安装本项目。

### macOS / Linux

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install ".[parquet]"
```

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install ".[parquet]"
```

> `.` 表示安装“当前目录中的 Python 项目”。
>
> `[parquet]` 表示同时安装 Parquet 输出所需的可选依赖，例如 pandas 和 pyarrow。

### 检查安装是否成功

```bash
globocan-fetch --help
```

如果能够正常显示 CLI 帮助信息，就说明 `globocan-fetch` 已经安装到当前虚拟环境中。

在开始一个正式研究项目之前，建议先确认当前观察到的 Cancer Today endpoint 和 metadata 仍可正常访问：

```bash
globocan-fetch verify --year 2024
globocan-fetch cancers --year 2024
globocan-fetch populations --year 2024
```

- `verify`：检查当前观察到的 Cancer Today endpoint 和 metadata 是否仍可正常访问；
- `cancers`：查看当前年份可用的 cancer/site metadata；
- `populations`：查看当前年份可用的人群 metadata。

### 第一次下载

示例：下载 2024 年女性乳腺癌发病、0–85+ 岁、全部返回人群的数据。

```bash
globocan-fetch download \
  --year 2024 \
  --metric incidence \
  --sex female \
  --cancer 20 \
  --age 0_17 \
  --format parquet \
  --output data/breast_female_2024
```

如果需要 CSV：

```bash
globocan-fetch download \
  --year 2024 \
  --metric incidence \
  --sex female \
  --cancer 20 \
  --age 0_17 \
  --format csv \
  --output data/breast_female_2024_csv
```

默认请求频率有意设置得较为保守。对于共享公共服务，不建议为了追求速度而大幅提高请求频率。

下载后的文件会写入 `--output` 指定的输出目录，例如 `data/breast_female_2024/`；下一节说明该目录的内容。

---

<!-- section: understanding-output -->
## 5. 如何阅读下载结果

一个标准输出目录类似：

```text
data/breast_female_2024/
├── tables/
│   └── incidence_female_can20_a0-17.parquet
├── DATA_DICTIONARY.md
├── manifest.json
└── .globocan-fetch/
    └── meta/
        ├── populations.json
        └── cancers.json
```

### `tables/`

这里是真正用于分析的 CSV 或 Parquet 数据文件。

**一张输出表固定一个“指标 × 性别 × 癌种 × 年龄范围”组合；每一行代表一个 population，而不是一个病例。**

例如：

```text
incidence_female_can20_a0-17.parquet
```

表示查询指定年龄范围下女性乳腺癌发病情况，不同 population 分别占据不同数据行。

### `manifest.json`

Manifest 是这个可复现数据快照的一部分。

其中记录的信息包括：

- 软件版本；
- dataset identity；
- GLOBOCAN 数据年份；
- 当前观察到的 endpoint base；
- 输出格式；
- 查询参数；
- 已完成任务；
- 空结果任务；
- 失败任务及其错误信息；
- 各输出文件行数；
- 输出文件 SHA-256；
- population metadata SHA-256；
- cancer metadata SHA-256；
- 时间戳。

建议将 manifest 与分析代码和派生数据一同保存。

### `DATA_DICTIONARY.md`

这是根据程序实际数据 schema 自动生成的双语字段说明。

它解释每一个公共输出字段，并用于降低代码 schema 与文档逐渐不一致的风险。

### `.globocan-fetch/meta/`

这里保存当前输出数据所使用的人群和癌种 metadata。

这些 metadata 属于本次数据获取上下文的一部分。在已经下载出结果后，不应随意替换而继续向同一数据快照中追加结果。

---

<!-- section: file-naming -->
## 6. 文件命名规则

例如：

```text
incidence_female_can20_a0-17.parquet
```

| 部分 | 含义 |
|---|---|
| `incidence` | 指标 |
| `female` | 性别 |
| `can20` | GCO Cancer Today cancer/site code 20 |
| `a0-17` | 年龄索引 0 至 17 |
| `parquet` | 输出格式 |

一个非常容易误解的地方是：

```text
can20
```

这里表示 **GCO cancer/site 条目编号 20**，并不是 ICD-10 `C20`。

对于当前观察到的 GLOBOCAN 2024 metadata：

```text
GCO cancer/site code 20 -> Breast -> ICD C50
```

因此解释 `cancer_code` 时应始终结合癌种 metadata，而不是把数字直接当作 ICD。

---

<!-- section: data-dictionary -->
## 7. 数据字典

每一行对应一个 population 在指定指标、性别、癌种/site 和年龄范围下的数据。

当前公共 schema 共包含 28 个字段。

| 字段 | 来源 | 含义 | 单位/取值 | 注意事项 |
|---|---|---|---|---|
| `country_code` | GCO response | GCO 返回的人群编码 | 数字编码 | 国家通常对应相应 numeric population code；聚合人群拥有自己的 GCO code。不能假定每一行都是国家。 |
| `pop_label` | GCO population metadata | 人群可读名称 | 文本 | 例如 `China`、`World`、`Eastern Asia` 或某一 HDI 分组。 |
| `iso3` | GCO population metadata | ISO3 国家代码 | 如 `CHN`、`USA`；可为空 | 一般仅国家存在；聚合人群通常为空。 |
| `pop_level` | globocan-fetch 派生 | 标准化后的人群层级 | `country`、`world`、`continent`、`subregion`、`who`、`hdi`、`income`、`hub`、`other` 或 fallback `aggregate` | 根据 GCO population metadata 派生，并不是 rate response 中的原始字段。 |
| `grouping` | GCO population metadata | GCO metadata 中的人群 grouping/category | 文本；可为空 | 不应简单翻译为“大洲”；具体含义以原始 metadata 为准。 |
| `area_label` | GCO population metadata | GCO metadata 提供的地理/区域标签 | 文本；可为空 | 可能表示 UN 子区域等地理分组。 |
| `who_region` | GCO population metadata | WHO 区域标识 | 如 AFRO、EURO、WPRO；可为空 | 属于 metadata 分类，不是流行病学估计指标。 |
| `hdi_label` | GCO population metadata | HDI 分组标签 | 文本；可为空 | 是分类标签，不是某个国家的具体 HDI 数值。 |
| `income_label` | GCO population metadata | 世界银行收入分组标签 | 文本；可为空 | 是分类标签，不是实际收入数值。 |
| `sex` | 查询条件 / 标准化 | 查询性别 | `both`、`male`、`female` | 对一张输出表而言固定。 |
| `metric` | 查询条件 / 标准化 | 查询指标 | `incidence`、`mortality` | 对一张输出表而言固定。 |
| `cancer_code` | GCO cancer metadata | Cancer Today cancer/site 条目编码 | 整数 | 不是 ICD 编码。 |
| `cancer_label` | GCO cancer metadata | 癌种/site 可读名称 | 文本 | 例如 `Breast`。 |
| `ICD` | GCO cancer metadata | GCO 对该癌种/site 定义给出的 ICD 信息 | 文本/编码范围 | 可能是单一 ICD 编码，也可能是组合范围。 |
| `age_start_idx` | 查询条件 / 派生 | 起始五岁年龄组索引 | `0`–`17` | 0-based。 |
| `age_end_idx` | 查询条件 / 派生 | 结束五岁年龄组索引 | `0`–`17` | 包含该年龄组，即 inclusive。 |
| `age_label` | globocan-fetch 派生 | 查询年龄范围的人类可读标签 | 如 `0-85+`、`65-69` | 描述当前表格所查询的年龄范围。 |
| `total` | GCO response 或派生 | 估计新发病例数或死亡数 | count | 重建的 2024 年高龄行使用相邻累计计数之差。 |
| `total_pop` | GCO response 或派生 | 当前性别和年龄范围对应的人口分母 | 人数 | 重建的 2024 年高龄行使用相邻累计人口数之差。 |
| `asr` | GCO response 或派生 | Age-Standardized Rate (World) | 通常每 100,000 人 | 重建的单年龄层行使用派生粗率；不可跨年龄段相加。 |
| `crude_rate` | GCO response 或派生 | 粗率 | 通常每 100,000 人 | 重建的高龄行按 `total / total_pop × 100,000` 计算；直接响应保留上游的取整结果。 |
| `cum_risk` | GCO response 或派生 | API 返回的当前查询年龄区间累计风险；重建的封闭五岁组使用标准累计率公式换算 | 百分比（%） | upstream key 缺失时保持 null；查询终点包含开放式 85+ 时 API 不返回该字段。 |
| `cum_risk_74` | GCO response | 根据观测 API 行为，该累计风险字段在 74 岁截断，同时保留查询起始年龄 | 百分比（%） | 不一定从出生开始：查询从 70 岁起时表示 70–74 岁。 |
| `rank` | GCO response | 当前 API 查询上下文返回的排序值 | 整数/可为空 | 依赖具体查询上下文，不应脱离原始 metric / sex / age / cancer 条件解释为固定“全球排名”。 |
| `ui_lower` | GCO response `ui.low` | Cancer Today 返回的估计病例数或死亡数（`total`）95%不确定性区间下限 | count；可为空 | 不是 ASR、粗率或累计风险的区间。 |
| `ui_upper` | GCO response `ui.high` | Cancer Today 返回的估计病例数或死亡数（`total`）95%不确定性区间上限 | count；可为空 | 缺失或不可用的边界保持 null。 |
| `ui_status` | 派生 QC | 上游人数 UI 的可用性与一致性状态 | `complete`、`incomplete`、`not_provided`、`point_outside_interval` | 即使点估计超出区间也保留原始数值边界。 |
| `point_within_ui` | 派生 QC | `total` 是否位于有限数值 UI 边界之内 | boolean；可为空 | 边界或点估计不可用时为 null；缺失不等于 false。 |

### 95%不确定性区间（95% uncertainty interval，schema v3）

`ui_lower` 和 `ui_upper` 是 Cancer Today 返回的估计人数（`total`）95%不确定性区间。默认从同一次 rate response 保存，不增加 HTTP 请求，也不需要 `--include-ui` 开关。

当前公开 API 的许多全年龄估计带有 UI；年龄限制请求可能不提供 UI。工具原样保留这种可用性，不推算年龄别区间。已观察的全年龄结直肠汇总癌种 41（Colorectum）同样不返回 UI。重建的 75–79、80–84 和 85+ 行上下界为空、`ui_status=not_provided`、`point_within_ui=null`，manifest provenance 中列出不可用的 UI 字段。工具不会复制全年龄区间、按比例分配、插值、跨癌种相加或跨累计年龄查询相减。

- `complete`：有限数值上下界和有效 `total`，满足 `low <= total <= high`。
- `point_outside_interval`：上下界和 `total` 有效，但点估计超出区间。正人数搭配 `0–0` UI 的异常原样保存并标记。
- `incomplete`：存在 `ui`，但边界缺失、null、非数值或非有限；`total` 不可用也无法执行区间内外检查。有效边界仍保留。
- `not_provided`：response 中完全没有 `ui` 字段。

真实响应示例（中国女性乳腺癌发病，2026-10-23 核查；省略其他列）：

```csv
country_code,sex,metric,cancer_code,age_label,total,ui_lower,ui_upper,ui_status,point_within_ui
156,female,incidence,20,0-85+,375808,373555,378075,complete,True
156,female,incidence,20,50-54,59957,,,not_provided,
```

上下界为空表示该查询的公开 API **没有提供不确定性区间**，不表示不确定性为零。上游提供但不可用的边界也输出 null，以 `incomplete` 区分。四个新字段追加在现有列之后。schema v3 拒绝续写 schema v2 输出目录；请使用新目录重新下载，工具不会迁移或覆盖旧 v2 文件。

<!-- concept: cum-risk-fields-differ -->

`cum_risk` 与 `cum_risk_74` 是两个不同的 upstream 字段，不会互相作为 fallback。IARC 将累计风险描述为指定年龄跨度内、假设没有其他死亡原因时发病或死亡的概率，由累计率计算。GCO API 的观测结果显示，`cum_risk` 对应完整查询区间；查询终点包含 85+ 时该 key 缺失。`cum_risk_74` 在结束年龄超过 74 岁时保持不变，同时保留查询起点，例如 14_14 至 14_17 的值完全相同。这支持“从所选起始年龄至 74 岁的累计风险”这一解释，而不是始终代表出生至 74 岁。该字段级解释来自 API 观测，并非找到的 GLOBOCAN 2024 官方字段定义。

---

<!-- section: measures -->
## 8. 如何理解 GLOBOCAN 指标

### 估计数量：`total`

对于发病：

```text
total = 估计新发癌症病例数
```

对于死亡：

```text
total = 估计癌症死亡数
```

这些是 GLOBOCAN 的估计值，不应简单描述为某国癌症登记系统“实际观察到的完整病例总数”。

### 粗率：`crude_rate`

粗率将估计事件数量与对应人群规模联系起来。

概念上：

```text
crude rate ≈ total / total_pop × 100,000
```

粗率会受到人群年龄结构的明显影响。

### 世界人口年龄标化率：`asr`

ASR 通过年龄标化，使不同年龄结构人群之间的描述性比较更加合理。

通常以每 100,000 人表示。

<!-- concept: asr-not-additive -->

**不同年龄组或不同年龄范围的 ASR 不能直接相加。**

如果将多个互不重叠的五岁年龄组合并，可以加总病例数和人口数后重新计算粗率。

但 ASR 的重新计算需要相应的标准人口权重。

目前 `globocan-fetch` 不提供任意自定义年龄范围的自动 ASR 重算流程。

### 累积风险：`cum_risk` 与 `cum_risk_74`

IARC 将指定年龄跨度内的累计风险定义为假设没有其他死亡原因时发病或死亡的概率。累计率是该跨度内逐年年龄别率之和；使用五岁年龄组时假设组内年龄别率恒定。若累计率以百分比表示，换算公式为 `risk (%) = 100 × (1 − exp(−cumulative_rate / 100))`；若累计率以每 100,000 人的率表示，则为 `100 × (1 − exp(−cumulative_rate_per_100000 / 100000))`。

`cum_risk` 表示 API 返回的所选查询区间风险。`cum_risk_74` 是单独保留的 API 字段；原始响应显示它在 74 岁截断但保留查询起点。该行为解释仍是基于 API 观测，而非 IARC 对字段的明确定义。重建 75–79 与 80–84 行时，程序使用重建的五岁组粗率和标准公式计算 `cum_risk`；85+ 是无固定宽度的开放区间，因此为 null。重建行的 `cum_risk_74` 为 null，因为其查询上下文与高龄组不等价。

Cancer Today 表格在封闭年龄区间显示 “Cum. risk”，对应 `cum_risk`；当查询终点为开放式 85+ 时，该字段缺失，网页改为显示 “Cum. risk 74”，取自 `cum_risk_74`（World 观测值：70–79 显示 1.8，对应 API `cum_risk=1.84`；70–85+ 显示 0.90，对应 API `cum_risk_74=0.90`）。

---

<!-- section: population-hierarchy -->
## 9. 人群层级

`globocan-fetch` 根据 GCO population metadata 派生 `pop_level`，从而更容易区分同一表中的国家和聚合人群。

可能出现：

| `pop_level` | 含义 |
|---|---|
| `country` | 单个国家 |
| `world` | 全球 |
| `continent` | 大洲聚合 |
| `subregion` | UN 等区域聚合 |
| `who` | WHO 区域 |
| `hdi` | HDI 分组 |
| `income` | 世界银行收入分组 |
| `hub` | GICR hub 分组 |
| `other` | 其他已识别聚合类别 |
| `aggregate` | 未映射到已知类别时的 fallback 聚合层级 |

<!-- concept: country-filter -->

进行国家排名、国家层面的相关分析或国家散点图之前，应明确筛选：

```python
countries = df[df["pop_level"] == "country"]
```

否则 World、大洲、WHO 区域、HDI 分组、收入分组等聚合行可能被错误混入“国家分析”。

查看当前人群 metadata：

```bash
globocan-fetch populations --year 2024
globocan-fetch populations --year 2024 --level country
globocan-fetch populations --year 2024 --level hdi
```

---

<!-- section: cancer-definitions -->
## 10. 癌种定义

GCO 的 `cancer_code` 与 ICD 编码不是同一种编码。

<!-- concept: cancer-code-not-icd -->

```text
cancer_code ≠ ICD
```

例如：

```text
GCO cancer/site code 20 -> Breast -> C50
```

`cancer_code` 表示 Cancer Today metadata 中的一个 cancer/site entry。

字段 `ICD` 则描述该 entry 对应的 ICD 定义。

部分 cancer/site entries 是组合或汇总类别，而不是单一解剖部位癌种。

因此不建议在分析代码中长期人工维护一份固定癌种列表，而应查看所用年份的 metadata：

```bash
globocan-fetch cancers --year 2024
```

---

<!-- section: age-groups -->
## 11. 年龄组

Cancer Today 年龄查询使用零起始的五岁年龄组索引：

| 索引 | 年龄 |
|---:|---|
| 0 | 0–4 |
| 1 | 5–9 |
| 2 | 10–14 |
| 3 | 15–19 |
| 4 | 20–24 |
| 5 | 25–29 |
| 6 | 30–34 |
| 7 | 35–39 |
| 8 | 40–44 |
| 9 | 45–49 |
| 10 | 50–54 |
| 11 | 55–59 |
| 12 | 60–64 |
| 13 | 65–69 |
| 14 | 70–74 |
| 15 | 75–79 |
| 16 | 80–84 |
| 17 | 85+ |

例如：

```text
0_14   -> 0–74
0_17   -> 0–85+
13_13  -> 65–69
```

查询：

```text
0_17
```

**并不会返回 18 行年龄组。**

它表示一次针对整个 0–85+ 年龄范围的聚合查询，不同数据行仍然对应不同 population。

如果需要逐五岁年龄组数据，需要分别请求五岁年龄范围。

`five_year` 预设会生成全部 18 个索引，但本工具使用的 rate 接口对女性乳腺癌发病和男性肺癌死亡的直接查询 `15_15`、`16_16`、`17_17` 返回 `dataset=[]`。当单个 75+ 年龄组的直接查询为空时，下载器会用相邻累计查询（`0_n` 减去 `0_(n-1)`）重建，并在 `manifest.json` 记录来源。病例/死亡数和人口数通过差值重建，粗率重新计算；单一年龄层的 ASR 等于该层率；封闭五岁组的累计风险使用 IARC 标准公式计算。开放式 85+ 的累计风险为 null；重建组的 `cum_risk_74` 和 `rank` 也为 null。具体证据和公式核查见 `docs/api-observations.md`。使用结果前仍应检查 manifest 中的 `empty` 和 `failed`。

该 fallback 仅适用于 2024 年且直接响应为空的情况。若累计响应的人群键不一致、必要计数无效或差值为负，任务会记为 `failed`，不会静默丢弃人群。若一次请求中三个 75+ 年龄组均需重建，写出文件前会检验其计数与人口数之和是否等于可得的累计 75+ 差值。这是内部算术一致性检查，并非另一条 GCO 官方估计。manifest 会记录 `direct_query`、其空响应、累计来源、派生字段和不可得字段。旧 manifest 中已标空的 2024 年高龄任务会重新尝试，其他空任务仍跳过。

CLI 还支持预定义类别，例如：

```bash
--age cumulative
--age five_year
```

---

<!-- section: analysis-recipes -->
## 12. 常见分析示例

### 读取 Parquet

```python
import pandas as pd

df = pd.read_parquet(
    "data/breast_female_2024/tables/incidence_female_can20_a0-17.parquet"
)
```

### 读取 CSV

```python
import pandas as pd

df = pd.read_csv(
    "data/breast_female_2024_csv/tables/incidence_female_can20_a0-17.csv"
)
```

### 仅保留国家

```python
countries = df[df["pop_level"] == "country"]
```

### 筛选 World

```python
world = df[df["pop_level"] == "world"]
```

在适用情况下，也可以：

```python
world = df[df["country_code"] == 900]
```

### 筛选中国

```python
china = df[df["iso3"] == "CHN"]
```

### 按 ASR 对国家排序

```python
ranking = (
    df[df["pop_level"] == "country"]
    .sort_values("asr", ascending=False)
    [["pop_label", "total", "asr"]]
)
```

### 使用五岁年龄组数据

如果已经下载各个 five-year age group，可以合并所需文件，再使用 `age_start_idx`、`age_end_idx` 或 `age_label` 筛选。

### 汇总病例数和人口并计算粗率

对于同一个 population / cancer / sex / metric 下多个互不重叠的五岁年龄组：

```python
agg = (
    df.groupby(["country_code", "pop_label"], as_index=False)
    .agg(
        total=("total", "sum"),
        total_pop=("total_pop", "sum"),
    )
)

agg["crude_rate"] = agg["total"] / agg["total_pop"] * 100_000
```

**不要对 ASR 进行加总。**

重新计算 ASR 需要正确的标准人口权重。

---

<!-- section: common-pitfalls -->
## 13. 常见误区

1. **把聚合人群混入国家分析。**  
   国家层面分析应先筛选 `pop_level == "country"`。

2. **将多个 ASR 相加。**  
   不同年龄组的 ASR 不可直接求和。

3. **把 `total` 当成实际登记病例总数。**  
   GLOBOCAN 提供的是估计癌症负担。

4. **把 `cancer_code` 当成 ICD。**  
   `cancer_code` 是 Cancer Today metadata entry code。

5. **把 `hdi_label` 当成 HDI 数值。**  
   它只是分类标签。

6. **把 `income_label` 当成实际收入。**  
   它是收入分组分类。

7. **认为一张表代表一个国家。**  
   一张表代表一组查询条件，每行才代表一个 population。

8. **认为任意 sex × cancer 组合都有数据。**  
   性别特异癌种的不匹配查询可能返回空 dataset。

9. **把 `cum_risk_74` 当成当前年龄范围的风险。**  
   根据 API 观测，它在 74 岁截断但保留查询起始年龄。

10. **把数据年份和下载日期混为一谈。**  
    2024 年估计数据完全可能在之后下载或更新。

11. **认为仅写“GLOBOCAN 2024”就描述了全部版本上下文。**  
    正式研究还应核对 Cancer Today 当前官方发布/版本信息。

12. **认为当前观察到的 endpoint 永久不变。**  
    Cancer Today 网页应用所使用的请求方式未来可能改变。

---

<!-- section: reproducibility -->
## 14. 可复现性

每一个下载目录都会维护 `manifest.json`。

Manifest schema v3 用于记录本地数据快照的身份与状态，包括：

- 软件版本；
- schema version；
- GLOBOCAN 数据年份；
- 当前观察到的 endpoint base；
- 输出格式；
- 查询参数；
- 已完成任务；
- 空结果任务；
- 输出文件行数；
- 输出文件 SHA-256；
- population metadata SHA-256；
- cancer metadata SHA-256；
- 时间戳。

程序会主动避免几类容易破坏复现性的混用。

如果已有输出目录对应的年份、endpoint、输出格式或 schema identity 与新的请求不同，程序会拒绝继续使用该目录，而不是静默复用旧的 completed task。

如果已有结果存在，此后使用 `--refresh-meta` 得到的 metadata 与原快照 hash 不一致，程序也不会继续将新 metadata 与旧结果混合。

此时应创建新的 output directory。

可以完全离线检查一个本地数据快照：

```bash
globocan-fetch inspect data/breast_female_2024
```

建议将 manifest 与以下内容一起保存：

- 分析代码；
- 派生数据集；
- 统计结果；
- 项目文档。

Manifest 记录的是本地数据获取上下文，但不能代替正式论文中对 Cancer Today 官方版本信息的核实。

---

<!-- section: technical-notes -->
## 15. 技术说明

当前工具基于公开 Cancer Today 网页应用所使用的请求模式。

概念上，相关资源位于：

```text
https://gco-api.iarc.fr/api/globocan/v3/{year}/
```

默认 endpoint 跟随当前 Cancer Today 前端（2026-10-23 核查）。可在 `download`、`verify`、`cancers` 或 `populations` 使用 `--api-base`，完整 URL 需包含年份：

```bash
globocan-fetch verify --year 2024 --api-base https://gco-api.iarc.fr/api/globocan/v3/2024
```

实际使用的 base URL 写入 manifest 和 dataset identity；不会静默 fallback 到旧 `gateway_prod` endpoint。修改 endpoint 必须使用新输出目录。UI provenance 记录 `uncertainty_intervals.source = gco_response.ui` 和 `inferred_when_missing = false`。


目前观察到的 metadata 资源包括：

```text
meta/populations/all/
meta/cancers/all/
```

rate 请求目前类似：

```text
data/rate/{metric_code}/{sex_code}/all/{cancer_code}/
    ?ages_group={start_idx}_{end_idx}
```

当前标准化映射：

```text
incidence -> 0
mortality -> 1

both   -> 0
male   -> 1
female -> 2
```

这些请求可以从公开网页应用中观察到，并不意味着 IARC 承诺将其作为长期稳定的公共 API。

开始新的数据项目前建议运行：

```bash
globocan-fetch verify --year 2024
```

更底层的实现说明见：

```text
docs/api-observations.md
```

全量 preset 的任务数由运行时实际维度计算：

```text
metrics × sexes × cancer/site metadata entries × age combinations
```

对于目前核验的 GLOBOCAN 2024 metadata，这对应 8,856 个查询组合。

不能假定其他年份也一定是 8,856。

---

<!-- section: citation-terms -->
## 16. 引用与数据条款

GLOBOCAN 数据、Cancer Today 网站材料以及相关 IARC/WHO 资源具有其自身的署名、使用和再分发条件。

本仓库中的 MIT License **仅适用于代码**，不适用于通过本工具下载的 GLOBOCAN 数据。

在发表研究或公开再分发下载数据、派生数据之前，应：

1. 阅读当前 GCO/IARC 数据使用条款；
2. 引用 GLOBOCAN / Global Cancer Observatory 官方数据源；
3. 报告数据年份以及相应的官方发布/版本信息；
4. 报告访问日期；
5. 保留足够的查询和分析信息以支持研究复现。

本仓库不分发 GLOBOCAN 全量数据，也不应被用作 Cancer Today 数据集的公开镜像。

软件引用信息见：

```text
CITATION.cff
```

---

### 反馈与联系

如果 `globocan-fetch` 对你的研究或学习有帮助，欢迎在 GitHub 上点一个 ⭐ Star，让更多需要 GLOBOCAN 数据的研究者能够发现这个项目。

如果在使用过程中发现 bug、有使用上的疑问，或者有改进建议，欢迎提交 GitHub Issue，也可以通过邮件联系我：

**Li Hengxi — lihengxi8@gmail.com**

## 开发

安装开发依赖：

```bash
python -m pip install -e ".[parquet,dev]"
```

`-e` 表示 editable install，适合需要修改或开发项目代码的情况。

运行测试：

```bash
pytest
```

项目默认测试不应依赖下载完整 GLOBOCAN 数据。
