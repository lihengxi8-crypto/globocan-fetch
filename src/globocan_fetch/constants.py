from __future__ import annotations

TYPE_CODES = {"incidence": 0, "mortality": 1}
SEX_CODES = {"both": 0, "male": 1, "female": 2}
AGE_LABELS = {
    0: "0-4", 1: "5-9", 2: "10-14", 3: "15-19", 4: "20-24", 5: "25-29",
    6: "30-34", 7: "35-39", 8: "40-44", 9: "45-49", 10: "50-54", 11: "55-59",
    12: "60-64", 13: "65-69", 14: "70-74", 15: "75-79", 16: "80-84", 17: "85+",
}
GROUPING_TO_LEVEL = {
    "Continents": "continent", "UN Regions": "subregion", "WHO region": "who",
    "HDI": "hdi", "World Bank Classification": "income", "GICR hub region": "hub",
    "Other": "other",
}


def age_label(start: int, end: int) -> str:
    if start == end:
        return AGE_LABELS[start]
    if end == 17:
        return f"{start * 5}-85+"
    return f"{start * 5}-{(end + 1) * 5 - 1}"


def age_combinations() -> list[dict]:
    cumulative = [(0, end) for end in range(2, 18)] + [(1, 17), (2, 17)]
    return (
        [{"start": start, "end": end, "label": age_label(start, end), "category": "cumulative"}
         for start, end in cumulative]
        + [{"start": i, "end": i, "label": age_label(i, i), "category": "five_year"}
           for i in range(18)]
    )

