import json
import os

class I18n:
    def __init__(self, locales_dir: str):
        self.locales_dir = locales_dir
        self.translations = {}
        self.load_translations()

    def load_translations(self):
        for filename in os.listdir(self.locales_dir):
            if filename.endswith(".json"):
                lang_code = filename.replace(".json", "")
                with open(os.path.join(self.locales_dir, filename), "r", encoding="utf-8") as f:
                    self.translations[lang_code] = json.load(f)

    def get(self, lang: str, key: str, **kwargs) -> str:
        lang_data = self.translations.get(lang, self.translations.get("ru", {}))
        text = lang_data.get(key, key)
        if kwargs:
            try:
                text = text.format(**kwargs)
            except KeyError:
                pass
        return text

i18n = I18n(os.path.join(os.path.dirname(os.path.dirname(__file__)), "locales"))
