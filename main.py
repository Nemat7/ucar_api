from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
from datetime import datetime
from typing import Optional

app = FastAPI()

# подключаемся к БД SQLite и создаём таблицу
def init_db():
    conn = sqlite3.connect("reviews.db")
    cursor = conn.cursor()
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                sentiment TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
    conn.commit()
    conn.close()


# тут мы определяем тональность отзыва по ключевым словам
def analyze_sentiment(text: str) -> str:
    text = text.lower()
    positive_words = {"хорош", "люблю", "отличн", "класс", "супер"}
    negative_words = {"плох", "ненавиж", "ужасн", "кошмар"}

    if any(word in text for word in positive_words):
        return "positive"
    elif any(word in text for word in negative_words):
        return "negative"
    return "neutural"


# модель для POST-запроса
class ReviewInput(BaseModel):
    text: str

# модель для ответа
class ReviewOutput(BaseModel):
    id: int
    text: str
    sentiment: str
    created_at: str



@app.get("/")
def read_root():
    return {"message": "Добро пожаловать в сервис анализа отзывов!"}


# добавляем отзыв
@app.post("/reviews", response_model=ReviewOutput)
def add_review(review: ReviewInput):
    sentiment = analyze_sentiment(review.text)
    created_at = datetime.utcnow().isoformat()

    conn = sqlite3.connect("reviews.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO reviews (text, sentiment, created_at) VALUES (?, ?, ?)",
        (review.text, sentiment, created_at),
    )
    review_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {
        "id": review_id,
        "text": review.text,
        "sentiment": sentiment,
        "created_at": created_at,
    }


# получаем отзывы (с фильтром по sentiment)
@app.get("/reviews", response_model=list[ReviewOutput])
def get_reviews(sentiment: Optional[str] = None):
    conn = sqlite3.connect("reviews.db")
    cursor = conn.cursor()

    if sentiment:
        cursor.execute(
            "SELECT id, text, sentiment, created_at FROM reviews WHERE sentiment = ?",
            (sentiment,),
        )
    else:
        cursor.execute("SELECT id, text, sentiment, created_at FROM reviews")

    reviews = [
        {
            "id": row[0],
            "text": row[1],
            "sentiment": row[2],
            "created_at": row[3]
        }
        for row in cursor.fetchall()
    ]
    conn.close()
    return reviews

# bнициализация БД при старте
init_db()
