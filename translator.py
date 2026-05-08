import threading
import translators as ts

_CACHE = {}
_LOCK = threading.Lock()


def _translate(source: str, target: str, text: str) -> str:
    if not text or not text.strip():
        return ""
    cache_key = (source, target, text)
    with _LOCK:
        if cache_key in _CACHE:
            return _CACHE[cache_key]
    try:
        # 15s timeout prevents hanging when network is slow/blocked
        result = ts.translate_text(
            text,
            from_language=source,
            to_language=target,
            timeout=15,
        )
        with _LOCK:
            _CACHE[cache_key] = result
        return result
    except Exception as e:
        raise RuntimeError(f"翻译失败: {e}")


def chinese_to_english(text: str) -> str:
    return _translate("zh", "en", text)


def english_to_chinese(text: str) -> str:
    return _translate("en", "zh", text)
