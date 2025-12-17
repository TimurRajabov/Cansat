from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

from .db import Base, engine, get_db
from .models import SensorData

app = FastAPI()

# ---------- CORS ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- create tables ----------
Base.metadata.create_all(bind=engine)

# ---------- Pydantic ----------
class SensorDataIn(BaseModel):
    hum: Optional[float] = None
    bmp_press: Optional[float] = None
    mq5: Optional[int] = None
    mq3: Optional[int] = None
    fused_temp: Optional[float] = None


# ---------- helpers ----------
def format_row(r: SensorData):
    return {
        "hum": r.hum,
        "bmp_press": r.bmp_press,
        "mq5": r.mq5,
        "mq3": r.mq3,
        "fused_temp": r.fused_temp,
        "date": r.timestamp.strftime("%d-%m-%Y"),
    }


def save_realtime(db: Session, source: str, data: SensorDataIn):
    row = SensorData(
        source=source,
        hum=data.hum,
        bmp_press=data.bmp_press,
        mq5=data.mq5,
        mq3=data.mq3,
        fused_temp=data.fused_temp,
    )
    db.add(row)
    db.commit()
    return row


# ---------- HOURLY SAVE ----------
def save_hourly(source: str):
    db = next(get_db())

    latest = db.execute(
        select(SensorData)
        .where(SensorData.source == source)
        .order_by(desc(SensorData.id))
        .limit(1)
    ).scalars().first()

    if latest:
        hourly = SensorData(
            source=source,
            hum=latest.hum,
            bmp_press=latest.bmp_press,
            mq5=latest.mq5,
            mq3=latest.mq3,
            fused_temp=latest.fused_temp,
            timestamp=datetime.utcnow(),  # фиксируем час
        )
        db.add(hourly)
        db.commit()

    db.close()


# ---------- SCHEDULER ----------
scheduler = BackgroundScheduler(timezone="UTC")

scheduler.add_job(lambda: save_hourly("room"), trigger="cron", minute=0)
scheduler.add_job(lambda: save_hourly("street"), trigger="cron", minute=0)

scheduler.start()


# ================= ROOM =================

@app.post("/api/room")
def add_room(data: SensorDataIn, db: Session = Depends(get_db)):
    save_realtime(db, "room", data)
    return {"status": "saved"}


@app.get("/api/room/latest")
def room_latest(db: Session = Depends(get_db)):
    r = db.execute(
        select(SensorData)
        .where(SensorData.source == "room")
        .order_by(desc(SensorData.id))
        .limit(1)
    ).scalars().first()

    if not r:
        return {"error": "no data"}

    return format_row(r)


@app.get("/api/room/all")
def room_all(db: Session = Depends(get_db)):
    rows = db.execute(
        select(SensorData)
        .where(SensorData.source == "room")
        .order_by(SensorData.timestamp)
    ).scalars().all()

    return [format_row(r) for r in rows]


# ================= STREET =================

@app.post("/api/street")
def add_street(data: SensorDataIn, db: Session = Depends(get_db)):
    save_realtime(db, "street", data)
    return {"status": "saved"}


@app.get("/api/street/latest")
def street_latest(db: Session = Depends(get_db)):
    r = db.execute(
        select(SensorData)
        .where(SensorData.source == "street")
        .order_by(desc(SensorData.id))
        .limit(1)
    ).scalars().first()

    if not r:
        return {"error": "no data"}

    return format_row(r)


@app.get("/api/street/all")
def street_all(db: Session = Depends(get_db)):
    rows = db.execute(
        select(SensorData)
        .where(SensorData.source == "street")
        .order_by(SensorData.timestamp)
    ).scalars().all()

    return [format_row(r) for r in rows]
