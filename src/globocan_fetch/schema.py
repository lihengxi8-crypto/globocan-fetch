"""The single, public schema for tables written by globocan-fetch."""
from __future__ import annotations

from dataclasses import dataclass


SCHEMA_VERSION = 3
UI_METADATA = {
    "source": "gco_response.ui",
    "label": "95% uncertainty interval",
    "inferred_when_missing": False,
}


@dataclass(frozen=True)
class FieldDefinition:
    name: str
    source: str
    nullable: bool
    unit_or_values: str
    description_en: str
    description_zh: str


def _f(name, source, nullable, unit, en, zh):
    return FieldDefinition(name, source, nullable, unit, en, zh)


FIELDS = (
    _f("country_code", "gco_response", False, "GCO population code", "Population code; aggregates have GCO-specific codes and are not necessarily countries.", "人群编码；聚合人群使用 GCO 专用编码，不一定代表国家。"),
    _f("pop_label", "gco_population_metadata", True, "text", "Population label from GCO metadata.", "GCO 元数据中的人群名称。"),
    _f("iso3", "gco_population_metadata", True, "ISO3 or null", "ISO3 for country populations; usually null for aggregates.", "国家人群的 ISO3；聚合人群通常为空。"),
    _f("pop_level", "derived", False, "country/world/continent/subregion/who/hdi/income/hub/other/aggregate", "Standardized level derived from GCO population metadata.", "根据 GCO 人群元数据派生的标准化层级。"),
    _f("grouping", "gco_population_metadata", True, "text", "GCO metadata grouping/category; not necessarily a continent.", "GCO 元数据分组/类别；不等同于大洲。"),
    _f("area_label", "gco_population_metadata", True, "text", "Geographic area label supplied by GCO metadata.", "GCO 元数据提供的地理区域标签。"),
    _f("who_region", "gco_population_metadata", True, "text", "WHO region label supplied by GCO metadata.", "GCO 元数据提供的 WHO 区域标签。"),
    _f("hdi_label", "gco_population_metadata", True, "category", "HDI group label, not a numeric HDI value.", "HDI 分组标签，不是连续 HDI 数值。"),
    _f("income_label", "gco_population_metadata", True, "category", "Income-group label, not an income value.", "收入组标签，不是收入数值。"),
    _f("sex", "query", False, "both/male/female", "Sex selected for the query.", "查询时选择的性别。"),
    _f("metric", "query", False, "incidence/mortality", "Measure selected for the query.", "查询时选择的指标。"),
    _f("cancer_code", "query", False, "GCO cancer/site code", "Cancer Today cancer/site code; this is not an ICD code.", "Cancer Today 癌种/部位编码；不是 ICD 编码。"),
    _f("cancer_label", "gco_cancer_metadata", True, "text", "Cancer/site label from GCO metadata.", "GCO 元数据中的癌种/部位名称。"),
    _f("ICD", "gco_cancer_metadata", True, "text", "ICD definition supplied by GCO metadata.", "GCO 元数据提供的 ICD 定义。"),
    _f("age_start_idx", "query", False, "0–17", "Start five-year age-band index (0 is 0–4; 17 is 85+).", "起始五岁年龄组索引（0 为 0–4；17 为 85+）。"),
    _f("age_end_idx", "query", False, "0–17", "End five-year age-band index.", "结束五岁年龄组索引。"),
    _f("age_label", "derived", False, "text", "Human-readable queried age range.", "人类可读的查询年龄范围。"),
    _f("total", "gco_response_or_derived", True, "count", "Estimated new cases or deaths; reconstructed 2024 high-age rows use adjacent cumulative count differences.", "估计新发病例数或死亡数；重建的 2024 年高龄行使用相邻累计计数之差。"),
    _f("total_pop", "gco_response_or_derived", True, "persons", "Population denominator; reconstructed 2024 high-age rows use adjacent cumulative population differences.", "人口分母；重建的 2024 年高龄行使用相邻累计人口数之差。"),
    _f("asr", "gco_response_or_derived", True, "per 100,000", "Age-standardized rate (World); reconstructed single-stratum rows use their derived crude rate. Do not sum across ages.", "世界标准人口年龄标化率；重建的单年龄层行使用派生粗率。不可跨年龄范围相加。"),
    _f("crude_rate", "gco_response_or_derived", True, "per 100,000", "Crude rate; reconstructed high-age rows use total / total_pop × 100,000.", "粗率；重建的高龄行按 total / total_pop × 100,000 计算。"),
    _f("cum_risk", "gco_response_or_derived", True, "percent", "Cumulative risk (%) for the queried age interval when provided by GCO; reconstructed closed five-year bands use the standard cumulative-rate conversion.", "GCO 提供的当前查询年龄区间累计风险（%）；重建的封闭五岁年龄组按标准累计率公式换算。"),
    _f("cum_risk_74", "gco_response", True, "percent", "GCO cumulative-risk field truncated at age 74 while retaining the queried starting age, based on observed API behavior; not necessarily birth through age 74.", "根据观测到的 API 行为，该字段在 74 岁截断但保留查询起始年龄；不一定表示从出生至 74 岁。"),
    _f("rank", "gco_response", True, "integer", "Context-dependent API ranking; interpret only with the original metric, sex, cancer and age query.", "依赖查询上下文的 API 排名；只能结合原始指标、性别、癌种和年龄查询解读。"),
    _f("ui_lower", "gco_response.ui.low", True, "count", "Lower bound of the 95% uncertainty interval for the estimated count (total), when returned by Cancer Today; not an ASR, crude-rate or cumulative-risk interval.", "Cancer Today 返回的估计病例数或死亡数（total）95%不确定性区间下限；若上游未提供则为空，不是标化率、粗率或累计风险的区间。"),
    _f("ui_upper", "gco_response.ui.high", True, "count", "Upper bound of the 95% uncertainty interval for the estimated count (total), when returned by Cancer Today; not an ASR, crude-rate or cumulative-risk interval.", "Cancer Today 返回的估计病例数或死亡数（total）95%不确定性区间上限；若上游未提供则为空，不是标化率、粗率或累计风险的区间。"),
    _f("ui_status", "derived_qc", False, "complete/incomplete/not_provided/point_outside_interval", "QC status: complete when finite bounds contain total; incomplete when UI is present but a bound or total is unusable; not_provided when ui is absent; point_outside_interval when total is outside the finite bounds. Upstream numeric bounds are preserved.", "质控状态：有限上下界包含 total 为 complete；存在 UI 但上下界或 total 不可用为 incomplete；无 ui 字段为 not_provided；total 超出有限上下界为 point_outside_interval。保留上游数值边界。"),
    _f("point_within_ui", "derived_qc", True, "boolean or null", "Whether total lies within the returned uncertainty interval; null when a complete numeric interval or usable total is unavailable.", "total 是否位于返回的不确定性区间内；无法取得完整数值区间或有效 total 时为空，不将缺失视为 false。"),

)
FIELD_NAMES = [field.name for field in FIELDS]


def data_dictionary_markdown() -> str:
    lines = ["# Data dictionary", "", f"Schema version: {SCHEMA_VERSION}", "", "One table fixes metric × sex × cancer × age range; each row represents one population, not one case.", "", "| Field | Source | Nullable | Unit / values | English description | 中文解释 |", "| --- | --- | --- | --- | --- | --- |"]
    lines += [f"| `{f.name}` | `{f.source}` | {'yes' if f.nullable else 'no'} | {f.unit_or_values} | {f.description_en} | {f.description_zh} |" for f in FIELDS]
    lines += ["", "`ui_lower` and `ui_upper` are 95% uncertainty intervals for the estimated count (`total`) as returned by Cancer Today. Missing intervals are not zero uncertainty. No age-specific or reconstructed intervals are inferred.", "", "ui_lower 和 ui_upper 仅对应估计人数；空值不表示不确定性为零。年龄限制请求、结直肠汇总或重建年龄组未返回的 UI 不会被复制、相加、相减、按比例分配或推算。"]
    return "\n".join(lines) + "\n"
