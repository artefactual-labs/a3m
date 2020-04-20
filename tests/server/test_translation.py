from a3m.server.translation import TranslationLabel
from a3m.server.translation import UNKNOWN_TRANSLATION_LABEL


def test_translation_label(mocker):
    mocker.patch("a3m.server.translation.FALLBACK_LANG", "en")
    tr = TranslationLabel({"en": "cat", "es": "gato"})
    assert repr(tr) == "TranslationLabel({'en': 'cat', 'es': 'gato'})"
    assert str(tr) == "cat"
    assert tr["es"] == "gato"
    assert tr["unexistent-lang-code"] == "cat"
    assert tr.get_label(lang="es") == "gato"
    assert tr.get_label(lang="is", fallback_label="köttur") == "köttur"
    assert tr.get_label(lang="??") == "cat"
    mocker.patch("a3m.server.translation.FALLBACK_LANG", "xx")
    assert tr.get_label(lang="yy") == UNKNOWN_TRANSLATION_LABEL


def test_translation_label_with_prepared_codes(mocker):
    mocker.patch("a3m.server.translation.FALLBACK_LANG", "en")
    tr = TranslationLabel({"en": "dog", "pt_BR": "cão"})
    assert tr.get_label(lang="en") == "dog"
    assert tr.get_label(lang="pt-br") == "cão"
    assert tr.get_label(lang="pt_BR") == "cão"


def test_translation_label_string(mocker):
    mocker.patch("a3m.server.translation.FALLBACK_LANG", "en")
    tr = TranslationLabel("cat")
    assert repr(tr) == "TranslationLabel({'en': 'cat'})"
