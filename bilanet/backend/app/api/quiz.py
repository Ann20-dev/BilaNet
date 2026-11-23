import json
import random
from pathlib import Path
from fastapi import APIRouter
from app.schemas.models import QuizChallengeRequest, QuizCheckRequest
from app.inference.provider import get_provider
from app import prompts

router = APIRouter()
QUESTIONS = json.loads((Path(__file__).resolve().parents[1] / "quiz" / "questions.json").read_text(encoding="utf-8"))


@router.get("/quiz/topics")
def topics():
    out = {}
    for q in QUESTIONS:
        out[q["topic"]] = out.get(q["topic"], 0) + 1
    return out


@router.get("/quiz/questions")
def questions(topic: str | None = None, level: str | None = None, count: int = 10):
    """Built-in multiple-choice questions. Instant and offline: no AI model needed."""
    pool = [q for q in QUESTIONS if (not topic or q["topic"] == topic) and (not level or q["level"] == level)]
    random.shuffle(pool)
    return pool[: max(1, min(count, 50))]


@router.post("/quiz/challenge")
def challenge(req: QuizChallengeRequest):
    """A new practice challenge written by the AI."""
    text = get_provider().generate(prompts.with_reply_language(prompts.quiz_challenge(req.topic, req.level), req.reply_language), system=prompts.system_prompt(req.reply_language))
    return {"challenge": text}


@router.post("/quiz/check")
def check(req: QuizCheckRequest):
    """The AI reviews the student's solution to a challenge."""
    text = get_provider().generate(prompts.with_reply_language(prompts.quiz_check(req.challenge, req.solution, req.language), req.reply_language), system=prompts.system_prompt(req.reply_language))
    return {"feedback": text}
