from typing import Optional, List
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.database import get_db
from backend.models import CardBlacklist
from backend.security_engine.card_analyzer import analyze_card_number
from backend.security_engine.bot_inspector import analyze_telegram_bot_or_username

router = APIRouter(prefix="/api/tools", tags=["Security Tools"])

class CheckCardRequest(BaseModel):
    card_number: str


class CheckBotRequest(BaseModel):
    username: str


from backend.security_engine.quiz_data import (
    ALL_QUIZ_DATA,
    LEVELS_META,
    get_level_meta,
    get_level_questions,
    analyze_user_behavior
)


class QuizSubmitRequest(BaseModel):
    level: Optional[int] = 1
    answers: List[int] # tanlangan variantlar indekslari
    question_ids: Optional[List[int]] = None



# Favqulodda SOS ma'lumotlar bazasi (O'zbekiston banklari va davlat organlari)
EMERGENCY_DATA = {
    "steps": [
        {
            "step": 1,
            "title_uz": "Kartani zudlik bilan bloklang!",
            "desc_uz": "Bank ilovangizga (Click, Payme, Uzum) kiring va kartani 'Bloklash' tugmasini bosing yoki bank koll-markaziga qo'ng'iroq qiling."
        },
        {
            "step": 2,
            "title_uz": "SMS va login parollarni yangilang!",
            "desc_uz": "Agar Telegram kodini yuborgan bo'lsangiz, Telegram sozlamalaridan 'Faol sessiyalar' bo'limiga kirib barcha boshqa qurilmalarni uzib tashlang va 2 bosqichli parolni (Two-Step Verification) yoqing."
        },
        {
            "step": 3,
            "title_uz": "Huquq-tartibot organlariga murojaat qiling!",
            "desc_uz": "Ichki Ishlar Vazirligi Kiberxavfsizlik markaziga (102 yoki 1102) qo'ng'iroq qiling yoki ariza bilan murojaat qiling. Skrinshotlar va cheklarni saqlab qo'ying."
        }
    ],
    "banks_contacts": [
        {"name": "Click O'zbekiston", "phone": "+998 71 202-01-01", "short": "71 202-01-01"},
        {"name": "Payme O'zbekiston", "phone": "+998 71 200-02-02", "short": "71 200-02-02"},
        {"name": "Uzum Bank", "phone": "+998 78 777-07-07", "short": "78 777-07-07"},
        {"name": "Xalq Banki", "phone": "1106", "short": "1106"},
        {"name": "Agrobank", "phone": "1216", "short": "1216"},
        {"name": "Kapitalbank", "phone": "+998 71 200-15-15", "short": "71 200-15-15"},
        {"name": "Ipak Yo'li Banki", "phone": "1296", "short": "1296"},
        {"name": "TBC Bank", "phone": "1150", "short": "1150"},
        {"name": "Anorbank", "phone": "1290", "short": "1290"},
        {"name": "O'zmilliybank (NBU)", "phone": "1344", "short": "1344"},
        {"name": "IIV Kiberxavfsizlik Markazi", "phone": "1102", "short": "1102 / 102"}
    ]
}

@router.get("/quiz-levels")
async def get_quiz_levels():
    """10 ta kiber-savodxonlik darajasi haqida ma'lumot."""
    result = []
    for lvl in range(1, 11):
        meta = get_level_meta(lvl)
        result.append({
            "level": lvl,
            "title": meta["title"],
            "difficulty": meta["difficulty"],
            "badge": meta["badge"],
            "description": meta["desc"],
            "question_count": 10
        })
    return {"levels": result}


@router.get("/quiz-questions")
async def get_quiz(level: int = 1, randomize: bool = True):
    """
    Belgilangan daraja uchun 10 ta savolni olish.
    Har safar har xil tartibda (randomize=True).
    """
    lvl = max(1, min(10, level))
    questions = get_level_questions(lvl, randomize=randomize)
    return {
        "level": lvl,
        "level_meta": get_level_meta(lvl),
        "total_questions": len(questions),
        "questions": [
            {
                "id": q["id"],
                "title": q["title"],
                "scenario": q["scenario"],
                "question": q["question"],
                "behavior_type": q["behavior_type"],
                "options": [
                    {
                        "index": o_idx,
                        "text": opt["text"],
                        "behavior": opt["behavior"]
                    } for o_idx, opt in enumerate(q["options"])
                ]
            } for q in questions
        ]
    }


@router.post("/quiz-submit")
async def submit_quiz(payload: QuizSubmitRequest):
    """
    Daraja test natijalarini va psixologik xulq-atvorni hisoblash.
    """
    lvl = max(1, min(10, payload.level or 1))
    meta = get_level_meta(lvl)
    original_questions = ALL_QUIZ_DATA.get(lvl, [])
    q_map = {q["id"]: q for q in original_questions}

    eval_list = []
    if payload.question_ids:
        for qid in payload.question_ids:
            if qid in q_map:
                eval_list.append(q_map[qid])
    if not eval_list:
        eval_list = original_questions

    answers_history = []
    feedback = []
    correct_count = 0

    for i, q in enumerate(eval_list):
        user_choice = payload.answers[i] if i < len(payload.answers) else -1
        correct_idx = -1
        chosen_opt = None
        for o_idx, opt in enumerate(q["options"]):
            if opt["is_correct"]:
                correct_idx = o_idx
            if o_idx == user_choice:
                chosen_opt = opt

        is_right = (user_choice == correct_idx) and (user_choice != -1)
        if is_right:
            correct_count += 1

        chosen_behavior = chosen_opt["behavior"] if chosen_opt else "Javob berilmadi"
        explanation = chosen_opt["explanation"] if chosen_opt else q["options"][correct_idx]["explanation"]

        answers_history.append({
            "behavior_type": q["behavior_type"],
            "is_correct": is_right,
            "behavior": chosen_behavior
        })

        feedback.append({
            "question_id": q["id"],
            "title": q["title"],
            "is_correct": is_right,
            "user_choice": user_choice,
            "correct_option_index": correct_idx,
            "behavior_chosen": chosen_behavior,
            "explanation": explanation
        })

    analysis = analyze_user_behavior(answers_history)

    return {
        "level": lvl,
        "level_title": meta["title"],
        "difficulty": meta["difficulty"],
        "correct_count": correct_count,
        "total": len(eval_list),
        "percentage": analysis["percent"],
        "rank": analysis["rank"],
        "rank_desc": analysis["rank_desc"],
        "psychological_profile": analysis["psychological_profile"],
        "next_level": lvl + 1 if lvl < 10 else None,
        "detailed_feedback": feedback
    }
