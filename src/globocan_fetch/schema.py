"""The single, public schema for tables written by globocan-fetch."""
from __future__ import annotations

from dataclasses import dataclass


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
    _f("total", "gco_response", True, "count", "Estimated new cases for incidence or estimated deaths for mortality.", "发病时为估计新发病例数；死亡时为估计死亡数。"),
    _f("total_pop", "gco_response", True, "persons", "Population denominator for the queried sex and age range.", "对应查询性别和年龄范围的人口分母。"),
    _f("asr", "gco_response", True, "per 100,000", "Age-standardized rate (World); do not sum across age ranges.", "世界标准人口年龄标化率；不可跨年龄范围相加。"),
    _f("crude_rate", "gco_response", True, "per 100,000", "Crude rate; approximately total / total_pop × 100,000, subject to source rounding.", "粗率；约为 total / total_pop × 100,000，可能受源端取整影响。"),
    _f("cum_risk_74", "gco_response", True, "percent", "Cumulative risk before age 75 (0–74), as returned by GCO; it is not the queried age interval risk.", "GCO 返回的 75 岁前（0–74）累计风险；并非当前查询年龄范围的风险。"),
    _f("rank", "gco_response", True, "integer", "Context-dependent API ranking; interpret only with the original metric, sex, cancer and age query.", "依赖查询上下文的 API 排名；只能结合原始指标、性别、癌种和年龄查询解读。"),
)
FIELD_NAMES = [field.name for field in FIELDS]


def data_dictionary_markdown() -> str:
    lines = ["# Data dictionary", "", "One table fixes metric × sex × cancer × age range; each row represents one population, not one case.", "", "| Field | Source | Nullable | Unit / values | English description | 中文解释 |", "| --- | --- | --- | --- | --- | --- |"]
    lines += [f"| `{f.name}` | `{f.source}` | {'yes' if f.nullable else 'no'} | {f.unit_or_values} | {f.description_en} | {f.description_zh} |" for f in FIELDS]
    return "\n".join(lines) + "\n"
