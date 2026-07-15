from app.services.feature_extractor import extract_lexical_features

def test_extract_lexical_features():
    features = extract_lexical_features("google.com")
    assert features["length"] == 6
    assert features["entropy"] > 0
    assert features["digit_ratio"] == 0.0

def test_extract_lexical_features_typosquatting():
    features = extract_lexical_features("g00gle.com")
    assert features["length"] == 6
    assert features["digit_ratio"] > 0.0
    assert features["keyword_match"] == True
    assert features["levenshtein_min"] == 2
