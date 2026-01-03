"""
Localization Helper Functions
"""
from locales.uz import UZ
from locales.ru import RU

LANGUAGES = {
    "uz": UZ,
    "ru": RU
}

LANGUAGE_NAMES = {
    "uz": "🇺🇿 O'zbekcha",
    "ru": "🇷🇺 Русский"
}


def get_text(key: str, lang: str = "uz", **kwargs) -> str:
    """
    Get localized text by key
    
    Args:
        key: Translation key
        lang: Language code (uz or ru)
        **kwargs: Format arguments
    
    Returns:
        Localized string
    """
    translations = LANGUAGES.get(lang, UZ)
    text = translations.get(key, UZ.get(key, key))
    
    if kwargs:
        try:
            return text.format(**kwargs)
        except KeyError:
            return text
    return text


def t(key: str, lang: str = "uz", **kwargs) -> str:
    """Shorthand for get_text"""
    return get_text(key, lang, **kwargs)
