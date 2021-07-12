from dpiste import OCR_test_series

def test_levenshtein_distance():
    assert OCR_test_series.levenshtein_distance("chien","niche") == 4
    assert OCR_test_series.levenshtein_distance("javawasneat","scalaisgreat") == 7
    assert OCR_test_series.levenshtein_distance("forward","drawrof") == 6
    assert OCR_test_series.levenshtein_distance("distance","eistancd") == 2
    assert OCR_test_series.levenshtein_distance("sturgeon","urgently") == 6
    assert OCR_test_series.levenshtein_distance("difference","distance") == 5
    assert OCR_test_series.levenshtein_distance("example","samples") == 3
    assert OCR_test_series.levenshtein_distance("bsfhebfkrn","bsthebtkrn") == 2
    assert OCR_test_series.levenshtein_distance("cie","cle") == 1