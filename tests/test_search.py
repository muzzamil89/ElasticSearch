from scripts.evaluate_and_test import get_ranked_ids_for_query


def test_aspirin_in_top3():
    ids = get_ranked_ids_for_query("aspirin 500 mg pain")
    assert "p001" in ids


def test_paracetamol_in_top3():
    ids = get_ranked_ids_for_query("paracetamol fever")
    assert "p002" in ids


def test_antibiotic_in_top3():
    ids = get_ranked_ids_for_query("antibiotic for infections")
    assert "p003" in ids


def test_antihistamine_non_drowsy():
    ids = get_ranked_ids_for_query("non-drowsy antihistamine")
    # allow either loratadine (p004) or cetirizine (p010)
    assert ("p004" in ids) or ("p010" in ids)
