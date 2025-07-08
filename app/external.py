import os
from typing import Literal

import httpx
from dotenv import load_dotenv

load_dotenv()

APILAYER_API_KEY = os.getenv("APILAYER_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# APILayer endpoint for sentiment analysis
a_pilayer_url = "https://api.apilayer.com/sentiment/analysis"


async def analyze_sentiment(text: str) -> Literal["positive", "negative", "neutral", "unknown"]:
    """Return sentiment via APILayer; fallback to 'unknown' on failure."""
    if not APILAYER_API_KEY:
        return "unknown"

    headers = {"apikey": APILAYER_API_KEY}
    payload = {"text": text}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(a_pilayer_url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            # Assumes response like {"sentiment": "positive"}
            sentiment = data.get("sentiment", "unknown")
            if sentiment not in {"positive", "negative", "neutral"}:
                return "unknown"
            return sentiment  # type: ignore
    except Exception:  # noqa: BLE001
        return "unknown"


async def categorize_complaint(text: str) -> Literal["technical", "payment", "other"]:

    if OPENAI_API_KEY:
        try:
            import openai  # imported lazily so the package remains optional

            openai.api_key = OPENAI_API_KEY  # Works for <1.0 and >=1.0

            prompt = (
                "Определи категорию жалобы: \"" + text + "\". "
                "Варианты: техническая, оплата, другое. Ответ только одним словом."
            )

            # Используем современный клиент openai>=1.0 (AsyncOpenAI).
            from openai import AsyncOpenAI  # type: ignore

            async_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
            response = await async_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=1,
            )
            raw_answer = response.choices[0].message.content.strip().lower()

            if raw_answer is None:
                raise RuntimeError("Failed to obtain answer from OpenAI")

            # Нормализуем ответ: берём только первое слово, убираем знаки препинания
            answer = raw_answer.split()[0].strip(".,")

            # Расширенный мэппинг + частичное совпадение
            if answer.startswith("тех") or answer.startswith("tech"):
                return "technical"  # type: ignore
            if answer.startswith("оплат") or answer in {"payment", "pay"}:
                return "payment"  # type: ignore
            if answer in {"other", "другое"}:
                return "other"  # type: ignore

            # Неоднозначный ответ → логируем и переходим к эвристике ниже
            print(
                "[categorize] Unmapped answer from OpenAI:",
                raw_answer,
                "-> falling back to keyword heuristic",
                flush=True,
            )
        except Exception as exc:  # noqa: BLE001
            # Ошибки сети / квоты / пакета — переходим к локальной эвристике
            print("[categorize] OpenAI failure:", exc, "-> using keyword heuristic", flush=True)

    # ---------------------------------
    # 2) Keyword-based fallback heuristic
    # ---------------------------------
    lowered = text.lower()

    technical_kw = [
        "ошибка",
        "error",
        "сайт",
        "server",
        "сервер",
        "не работает",
        "не открывается",
        "500",
        "503",
    ]
    payment_kw = [
        "деньги",
        "оплат",
        "payment",
        "pay",
        "charge",
        "списал",
        "списали",
        "дважды",
    ]

    if any(k in lowered for k in technical_kw):
        return "technical"  # type: ignore
    if any(k in lowered for k in payment_kw):
        return "payment"  # type: ignore

    return "other"  # type: ignore 