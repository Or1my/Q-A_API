from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
import uuid
from .database import get_db, create_tables
from . import models
from contextlib import asynccontextmanager
from pydantic import BaseModel
from datetime import datetime 


@asynccontextmanager
async def app_lifespan(app: FastAPI): 
    create_tables()
    print("Таблицы созданы")
    yield
    print("Приложение останавливается")

app = FastAPI(title="Q&A API", lifespan=app_lifespan)

class QuestionBase(BaseModel):
    text:str

class QuestionCreate(QuestionBase):
    pass

class Question(QuestionBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class AnswerBase(BaseModel):
    text: str
    user_id: str

class AnswerCreate(AnswerBase):
    pass

class Answer(AnswerBase):
    id: int
    question_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class QuestionWithAnswers(Question):
    id: int
    text: str
    created_at: datetime
    answers: List[Answer] = []

    class Config:
        from_attributes = True

@app.get("/")
def root():
    return {"message": "Q&A API запущен"}

#Блок вопросов
@app.get("/questions/", response_model=List[Question])
def get_questions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    db.expire_all()
    qestions = db.query(models.Question).offset(skip).limit(limit).all()
    return qestions

@app.post("/questions/", response_model=Question)
def create_question(question: QuestionCreate, db: Session = Depends(get_db)):
    db_question = models.Question()
    db_question.text = question.text
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question

@app.get("/questions/{question_id}", response_model=QuestionWithAnswers)
def get_question(question_id: int, db: Session = Depends(get_db)):
    question = db.query(models.Question).filter(models.Question.id == question_id).first()
    if question is None:
        raise HTTPException(status_code=404, detail="Вопрос не найдет")
    #return question
    answers = db.query(models.Answer).filter(models.Answer.question_id == question_id).all()  # type: ignore

    return {
        "id": question.id,
        "text": question.text,
        "created_at": question.created_at,
        "answers": answers

    }
        

@app.delete("/questions/{question_id}")
def delete_questin(question_id: int, db: Session = Depends(get_db)):
    try:
        question = db.query(models.Question).filter(models.Question.id == question_id).first()
        if question is None:
            raise HTTPException(status_code=404, detail="Вопрос не найдет")
        db.execute(text("DELETE FROM answers WHERE question_id = :q_id"), {"q_id": question_id})
        db.execute(text("DELETE FROM questions WHERE id = :q_id"), {"q_id": question_id})
        db.commit()
        return {"message": "Question and its answers deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting question: {str(e)}")

#Блок ответов
@app.post("/questions/{question_id}/answers/", response_model=Answer)
def create_answer(question_id: int, answer: AnswerCreate, db: Session = Depends(get_db)):
    question =  question = db.query(models.Question).filter(models.Question.id == question_id).first()
    if question is None:
        raise HTTPException(status_code=404, detail="Вопрос не найдет")
    
    db_answer = models.Answer()
    db_answer.question_id = question_id
    db_answer.text = answer.text
    db_answer.user_id = answer.user_id or str(uuid.uuid4)
    db.add(db_answer)
    db.commit()
    db.refresh(db_answer)
    return db_answer

@app.get("/answers/{answer_id}", response_model=Answer)
def get_answer(answer_id: int, db: Session = Depends(get_db)):
    answer = db.query(models.Answer).filter(models.Answer.id == answer_id).first()
    if answer is None:
        raise HTTPException(status_code=404, detail="Ответ не найден")
    return answer

@app.delete("/answers/{answer_id}")
def delete_answer(answer_id: int, db: Session = Depends(get_db)):
    answer = db.query(models.Answer).filter(models.Answer.id == answer_id).first()
    if answer is None:
        raise HTTPException(status_code=404, detail="Ответ не найден")
    db.delete(answer)
    db.commit()
    return {"message": "Ответ успешно удален"}

#if __name__ == "__main__":
#    import uvicorn
#    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
 