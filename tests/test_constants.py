from globocan_fetch.constants import age_combinations, age_label


def test_age_labels_and_count():
    combos = age_combinations()
    assert len(combos) == 36
    assert age_label(0, 17) == "0-85+"
    assert age_label(17, 17) == "85+"
    assert sum(item["category"] == "cumulative" for item in combos) == 18

