# globocan-fetch

[English](README.md) | 中文

`globocan-fetch` 是一个用于**可复现下载与整理 GLOBOCAN Cancer Today 表格估计数据**的 Python 命令行工具。它把 GCO 页面中可观察到的数据请求封装成小范围、可限速、可恢复的下载流程，并将人群和癌种元数据补充到结果中，便于后续用 R、Python、Stata 或 DuckDB 分析。

> **项目状态：v0.1，研究用途。** 本项目使用的是从 GCO Cancer Today 网页应用观察到的请求路径，不应视为 IARC/WHO 承诺稳定的公开 API。开始正式项目或更新数据前，请先运行 `verify`；若网页、字段或使用条款变更，以官方网站为准。

## 它解决什么问题

GCO 网页可以交互式查看国家、癌种、性别、年龄段的指标，但要复现一组分析，手动导出很繁琐。本工具提供：

- 按“指标 × 性别 × 癌种 × 年龄段”检索数据；
- 每个请求使用 `populations=all`，当前会同时返回国家及 GCO 聚合人群，不必逐国循环请求；
- 自动缓存癌种、人群元数据，并补充人群名称、ISO3、地区/HDI/收入组等字段；
- 全局限速、网络重试和 `Retry-After` 等待，避免高频访问；
- 原子写入输出文件；中途中断后，可依据清单恢复未完成任务；
- 输出 CSV 或 Parquet，并生成含请求参数、完成状态与文件 SHA-256 的 `manifest.json`。

本仓库**不包含，也不分发 GLOBOCAN 原始或全量下载数据**。

## 安装

建议创建独立环境：

```bash
python -m venv .venv

# macOS / Linux
.venv/bin/python -m pip install -U pip
.venv/bin/python -m pip install -e ".[parquet,dev]"

# Windows PowerShell
.venv\Scripts\python -m pip install -U pip
.venv\Scripts\python -m pip install -e ".[parquet,dev]"
```

其中：

- 基础依赖只有 `requests`；
- 使用 `--format parquet` 需要 `pandas` 和 `pyarrow`；
- `dev` 安装额外包含测试工具。

安装完成后，以下两种调用等价：

```bash
globocan-fetch --help
python -m globocan_fetch.cli --help
```

## 第一次使用：先验证、再小范围下载

不要一开始就运行全量下载。先确认当前年份的端点和元数据可用：

```bash
globocan-fetch verify --year 2024
globocan-fetch cancers --year 2024
```

`verify` 会输出人群数量、癌种数量和实际端点基础地址；建议将输出保存到项目记录中。`cancers` 会列出可用癌种码、名称和 ICD 编码。

以下示例下载“2024 年、女性、乳腺癌、发病、0–85+ 岁、全部人群”的数据：

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

默认限速为全部请求合计每秒 1 次。输出目录类似：

```text
data/breast_female_2024/
├─ tables/
│  └─ incidence_female_can20_a0-17.parquet
├─ .globocan-fetch/meta/
│  ├─ populations.json
│  └─ cancers.json
└─ manifest.json
```

若希望使用通用文本格式，将 `--format parquet` 改成 `--format csv`。

## 常见下载示例

### 同时下载发病与死亡、多个癌种和年龄段

```bash
globocan-fetch download \
  --year 2024 \
  --metric incidence,mortality \
  --sex both,female \
  --cancer 20,39 \
  --age 0_2,0_17 \
  --format csv \
  --output data/example
```

参数中的名称和编码含义：

| 参数 | 示例 | 含义 |
| --- | --- | --- |
| `--metric` | `incidence,mortality` | 发病 / 死亡；可逗号分隔 |
| `--sex` | `both,male,female` | 两性合计 / 男 / 女；可逗号分隔 |
| `--cancer` | `20,39` | 癌种数字码；先用 `cancers` 查询 |
| `--age` | `0_2,0_17` | 年龄组起止索引；可逗号分隔 |
| `--output` | `data/example` | 输出目录，必填 |
| `--format` | `parquet` 或 `csv` | 输出格式 |
| `--rps` | `1` | 全局每秒请求数，默认 1 |

### 年龄段写法

五岁年龄组使用从 0 开始的索引：`0=0–4 岁`、`1=5–9 岁`、…、`17=85+ 岁`。

年龄段有三种等价写法：

```bash
--age 0_17       # 索引写法：0–85+
--age 0-85+      # 人类可读标签
--age cumulative # 全部 18 个累计年龄段
--age five_year  # 全部 18 个单独五岁组
```

### 全量下载

截至本项目整理时，全量任务为：2 个指标 × 3 个性别 × 41 个癌种 × 36 个年龄组合 = **8,856 次请求**。它需要显式确认：

```bash
globocan-fetch download \
  --year 2024 \
  --preset full \
  --yes \
  --format parquet \
  --output data/globocan_2024
```

全量下载时间受网络与服务端限制影响很大。请保持保守限速，不要为追求速度提高并发或请求频率；遇到失败时，直接用相同命令重新运行即可恢复未完成任务。

## 输出字段

每一行对应一个“人群 × 指标 × 性别 × 癌种 × 年龄段”组合。结果包含下列主要字段：

| 字段 | 含义 |
| --- | --- |
| `country_code` | GCO 人群码；国家通常为 ISO 数字码，聚合人群有专用编码 |
| `pop_label` / `iso3` | 人群名称 / 国家 ISO3；聚合人群的 `iso3` 为空 |
| `pop_level` | `country`、`world`、`continent`、`subregion`、`who`、`hdi`、`income` 等 |
| `grouping`、`area_label`、`who_region` | 人群分组和地理/WHO 信息 |
| `metric` / `sex` | `incidence` 或 `mortality`；`both`、`male`、`female` |
| `cancer_code` / `cancer_label` / `ICD` | 癌种编码、名称和 ICD 信息 |
| `age_start_idx` / `age_end_idx` / `age_label` | 年龄段索引和标签 |
| `total` / `total_pop` | 该年龄段的估计病例（或死亡）数 / 人口数 |
| `asr` | 世界标准人口年龄标化率（通常为每 10 万人） |
| `crude_rate` | 粗率（通常为每 10 万人） |
| `cum_risk_74` / `rank` | API 提供时的 0–74 岁累计风险 / 排名 |

部分指标在某些癌种、性别或人群下可能为空。性别特异癌种和不匹配性别的组合通常会返回空 `dataset`；工具将其记录到清单的 `empty`，不生成表格文件。

## 重要统计注意事项

- **不要把不同年龄组的 ASR 直接相加。** 若从五岁组汇总任意年龄范围，可以加总 `total` 和 `total_pop`，再计算粗率；ASR 必须使用相应标准人口权重重新计算。
- GLOBOCAN 是估计数据，适用于描述性比较时应完整报告数据版本、访问日期、癌种定义、年龄段和指标口径。
- 国家行与 World、HDI、收入组、区域等聚合行同在结果中。进行国家排名时，请筛选 `pop_level == "country"`，避免将聚合行混入。
- `manifest.json` 是复现的一部分。请与分析代码、派生数据一起保存，不要只保存最后导出的表格。

## 复现与断点续传

每次下载都会维护 `manifest.json`，其中包含：软件版本、年份、请求参数、端点基础地址、限速、已完成任务、空结果任务、每个输出文件的行数与 SHA-256。

网络中断或个别请求失败后，使用**相同的输出目录和命令**重跑即可；已记录完成的任务会跳过。若希望刷新当前元数据缓存，可增加：

```bash
globocan-fetch download ... --refresh-meta
```

如果你需要重新生成全部结果，请使用一个新的输出目录。这样可以保留旧版本的可复现快照，也可避免把不完整文件误当成新结果。

## 观察到的请求模型

本工具目前基于下列网页应用所使用的请求形态：

```text
GET https://gco.iarc.fr/gateway_prod/api/globocan/v3/{year}/meta/populations/all/
GET https://gco.iarc.fr/gateway_prod/api/globocan/v3/{year}/meta/cancers/all/
GET https://gco.iarc.fr/gateway_prod/api/globocan/v3/{year}/data/rate/
    {type}/{sex}/all/{cancer}/?ages_group={start}_{end}
```

编码为：`type=0` 发病、`type=1` 死亡；`sex=0` 两性、`sex=1` 男、`sex=2` 女。`populations=all` 的实际返回范围应以每次 `verify` 和元数据结果为准。更详细说明见 [docs/api-observations.md](docs/api-observations.md)。

## 数据使用、版权与引用

- 本项目的 MIT 许可证**只适用于代码**，不适用于通过工具获取的 GLOBOCAN/IARC/WHO 数据或网站材料。
- 请在下载、使用、发布或再分发数据前阅读 GCO/IARC 的最新条款；尤其不要将全量下载结果提交到本仓库、GitHub Release 或其他公开镜像，除非数据提供方明确允许。
- 论文、报告和衍生数据库应引用 GCO 官方数据源，并写明数据版本和访问日期；需要时还应引用对应的 GLOBOCAN 学术文献。
- 本工具与 IARC、WHO 或 GCO 没有隶属、认可或合作关系。

## 开发与发布

```bash
python -m pytest
python -m globocan_fetch.cli --help
```

首次发布 GitHub 前，请完成 [发布检查清单](docs/release-checklist.md)。建议在 README 顶部增加项目维护者、问题反馈渠道和推荐引用信息，并在 `CITATION.cff` 中替换你的 GitHub 仓库地址。

