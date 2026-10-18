"""Server-side vocabulary for text the backend sends on its own (emails).

The web UI has its own translations (frontend/messages/*.json); this only
covers what never goes through the frontend. Keep LANGUAGES in sync with the
frontend's project.inlang/settings.json locales.
"""

from typing import Literal, get_args


Language = Literal["en", "fr"]
LANGUAGES: tuple[str, ...] = get_args(Language)
DEFAULT_LANGUAGE: Language = "en"


MESSAGES: dict[str, dict[str, str]] = {
    "en": {
        "reset_email_subject": "Reset your Framily password",
        "reset_email_body": (
            "Hi {name},\n\n"
            "Someone (hopefully you) asked to reset your Framily password.\n"
            "Open this link to choose a new one:\n\n"
            "{link}\n\n"
            "The link expires in {minutes} minutes and can only be used once.\n"
            "If you didn't ask for this, you can ignore this email.\n"
        ),
    },
    "fr": {
        "reset_email_subject": "Réinitialisez votre mot de passe Framily",
        "reset_email_body": (
            "Bonjour {name},\n\n"
            "Quelqu'un (vous, espérons-le) a demandé à réinitialiser votre mot de passe Framily.\n"
            "Ouvrez ce lien pour en choisir un nouveau :\n\n"
            "{link}\n\n"
            "Le lien expire dans {minutes} minutes et ne peut être utilisé qu'une seule fois.\n"
            "Si vous n'êtes pas à l'origine de cette demande, vous pouvez ignorer cet email.\n"
        ),
    },
}


def t(language: str | None, key: str, **params) -> str:
    """Translate `key` into `language`, falling back to English."""
    vocabulary = MESSAGES.get(language or DEFAULT_LANGUAGE, MESSAGES[DEFAULT_LANGUAGE])
    template = vocabulary.get(key, MESSAGES[DEFAULT_LANGUAGE][key])
    return template.format(**params)
