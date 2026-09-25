from globocan_fetch.constants import age_combinations, age_label


def test_age_labels_and_count():
    combos = age_combinations()
    assert len(combos) == 36
    assert age_label(0, 17) == "0-85+"
    assert age_label(17, 17) == "85+"
    assert sum(item["category"] == "cumulative" for item in combos) == 18


def test_five_year_preset_includes_all_high_age_groups():
    five_year = [item for item in age_combinations() if item["category"] == "five_year"]
    assert len(five_year) == 18
    assert [(item["start"], item["end"]) for item in five_year] == [(i, i) for i in range(18)]
    assert [(item["start"], item["end"], item["label"]) for item in five_year[-3:]] == [
        (15, 15, "75-79"), (16, 16, "80-84"), (17, 17, "85+"),
    ]

