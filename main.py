import os
import csv
import io
import requests
from difflib import SequenceMatcher

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters


TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SHEET_CSV_URL = os.getenv("SHEET_CSV_URL")


def similarity(a, b):
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def load_answers():
    response = requests.get(SHEET_CSV_URL, timeout=10)
    response.raise_for_status()

    text = response.content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))

    answers = []
    for row in reader:
        question = row.get("Вопрос", "").strip()
        answer = row.get("Ответ", "").strip()

        if question and answer:
            answers.append({"question": question, "answer": answer})

    return answers


def find_answer(user_question):
    answers = load_answers()

    best_match = None
    best_score = 0

    for item in answers:
        score = similarity(user_question, item["question"])
        if score > best_score:
            best_score = score
            best_match = item

    if best_match and best_score >= 0.65:
        return best_match["answer"]

    return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет!\n\n"
        "Отправь вопрос из теста, а я попробую найти ответ в базе."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_question = update.message.text

    await update.message.reply_text("🔎 Ищу ответ в базе...")

    try:
        answer = find_answer(user_question)

        if answer:
            await update.message.reply_text(f"✅ Ответ:\n{answer}")
        else:
            await update.message.reply_text(
                "❌ Ответ не найден в базе.\n\n"
                "Отправь скриншот теста или напиши менеджеру."
            )

    except Exception:
        await update.message.reply_text(
            "⚠️ Сейчас не удалось проверить базу.\n"
            "Попробуй позже или напиши менеджеру."
        )


def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()


if __name__ == "__main__":
    main()
