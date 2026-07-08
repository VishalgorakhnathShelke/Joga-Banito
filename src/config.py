# src/config.py

import os
from dotenv import load_dotenv


load_dotenv()


def get_required_env(variable_name: str) -> str:
    """
    Read a required environment variable from .env.
    If missing, raise a clear error.
    """
    value = os.getenv(variable_name)

    if not value:
        raise ValueError(
            f"Missing required environment variable: {variable_name}. "
            f"Please check your .env file."
        )

    return value


def get_optional_env(variable_name: str, default_value: str) -> str:
    """
    Read an optional environment variable from .env.
    If missing, return default value.
    """
    return os.getenv(variable_name, default_value)


GEMINI_API_KEY = get_required_env("GEMINI_API_KEY")
GEMINI_MODEL = get_optional_env("GEMINI_MODEL", "gemini-2.5-flash")

GROQ_API_KEY = get_required_env("GROQ_API_KEY")
GROQ_MODEL = get_optional_env("GROQ_MODEL", "llama-3.3-70b-versatile")

TAVILY_API_KEY = get_required_env("TAVILY_API_KEY")
TAVILY_MAX_RESULTS = int(get_optional_env("TAVILY_MAX_RESULTS", "5"))

COUNTRY = get_optional_env("COUNTRY", "Australia")
TAX_AUTHORITY = get_optional_env("TAX_AUTHORITY", "Australian Taxation Office")
REGULATOR = get_optional_env("REGULATOR", "Tax Practitioners Board")
DEFAULT_TAX_YEAR = get_optional_env("DEFAULT_TAX_YEAR", "2025-2026")

APP_ENV = get_optional_env("APP_ENV", "development")
DEBUG = get_optional_env("DEBUG", "True").lower() == "true"


if __name__ == "__main__":
    print("Config loaded successfully.")
    print(f"Gemini model: {GEMINI_MODEL}")
    print(f"Groq model: {GROQ_MODEL}")
    print(f"Country: {COUNTRY}")
    print(f"Tax authority: {TAX_AUTHORITY}")
    print(f"Regulator: {REGULATOR}")
    print(f"Tax year: {DEFAULT_TAX_YEAR}")