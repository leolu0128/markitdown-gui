"""介面翻譯表的完整性測試。"""
import string

from gui import STRINGS


def test_both_languages_present():
    assert set(STRINGS) == {"zh", "en"}


def test_translation_keys_match():
    """兩種語言必須有完全相同的鍵，避免切換時漏字。"""
    assert set(STRINGS["zh"]) == set(STRINGS["en"])


def test_format_placeholders_match_across_languages():
    """同一個鍵在中英文的 {placeholder} 必須一致，否則 .format() 會出錯。"""
    for key in STRINGS["zh"]:
        zh_fields = {f for _, f, _, _ in string.Formatter().parse(STRINGS["zh"][key]) if f}
        en_fields = {f for _, f, _, _ in string.Formatter().parse(STRINGS["en"][key]) if f}
        assert zh_fields == en_fields, f"placeholder mismatch on {key!r}"
