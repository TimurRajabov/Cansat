from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from .db import Base, engine, get_db
from .models import SensorData, CansatData

app = FastAPI()

app.add_middleware(

    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

class CansatDataIn(BaseModel):
    gps_valid: Optional[bool] = None
    bmp_valid: Optional[bool] = None
    dht_valid: Optional[bool] = None
    avg_temp: Optional[float] = None
    bmp_temp: Optional[float] = None
    bmp_press: Optional[float] = None
    dht_temp: Optional[float] = None
    dht_hum: Optional[float] = None
    gps_lat: Optional[float] = None
    gps_lon: Optional[float] = None
    accel_x: Optional[int] = None
    accel_y: Optional[int] = None
    accel_z: Optional[int] = None
    gyro_x: Optional[int] = None
    gyro_y: Optional[int] = None
    gyro_z: Optional[int] = None

class SensorDataIn(BaseModel):
    hum: Optional[float] = None
    bmp_press: Optional[float] = None
    mq5: Optional[int] = None
    mq3: Optional[int] = None
    fused_temp: Optional[float] = None

def format_row(r: SensorData):

    return {

        "hum": r.hum,
        "bmp_press": r.bmp_press,
        "mq5": r.mq5,
        "mq3": r.mq3,
        "fused_temp": r.fused_temp,
        "date": r.timestamp.strftime("%d-%m %H:%M"),

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

            timestamp=datetime.utcnow(),

        )

        db.add(hourly)

        db.commit()

    db.close()

scheduler = BackgroundScheduler(timezone="UTC")

scheduler.add_job(lambda: save_hourly("room"), trigger="cron", minute=0)

scheduler.add_job(lambda: save_hourly("street"), trigger="cron", minute=0)

scheduler.start()

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

        .order_by(SensorData.timestamp){}

    ).scalars().all()

    return [format_row(r) for r in rows]


def format_cansat(r: CansatData):
    return {
        "gps_valid": r.gps_valid,
        "bmp_valid": r.bmp_valid,
        "dht_valid": r.dht_valid,
        "avg_temp": r.avg_temp,
        "bmp_temp": r.bmp_temp,
        "bmp_press": r.bmp_press,
        "dht_temp": r.dht_temp,
        "dht_hum": r.dht_hum,
        "gps_lat": r.gps_lat,
        "gps_lon": r.gps_lon,
        "accel_x": r.accel_x,
        "accel_y": r.accel_y,
        "accel_z": r.accel_z,
        "gyro_x": r.gyro_x,
        "gyro_y": r.gyro_y,
        "gyro_z": r.gyro_z,
        "date": r.timestamp.strftime("%d-%m %H:%M:%S"),
    }


@app.post("/api/cansat")
def add_cansat(data: CansatDataIn, db: Session = Depends(get_db)):
    row = CansatData(
        gps_valid=data.gps_valid,
        bmp_valid=data.bmp_valid,
        dht_valid=data.dht_valid,
        avg_temp=data.avg_temp,
        bmp_temp=data.bmp_temp,
        bmp_press=data.bmp_press,
        dht_temp=data.dht_temp,
        dht_hum=data.dht_hum,
        gps_lat=data.gps_lat,
        gps_lon=data.gps_lon,
        accel_x=data.accel_x,
        accel_y=data.accel_y,
        accel_z=data.accel_z,
        gyro_x=data.gyro_x,
        gyro_y=data.gyro_y,
        gyro_z=data.gyro_z,
    )
    db.add(row)
    db.commit()
    return {"status": "saved"}


@app.get("/api/cansat/latest")
def cansat_latest(db: Session = Depends(get_db)):
    r = db.execute(
        select(CansatData).order_by(desc(CansatData.id)).limit(1)
    ).scalars().first()
    if not r:
        return {"error": "no data"}
    return format_cansat(r)


@app.get("/api/cansat/all")
def cansat_all(db: Session = Depends(get_db)):
    rows = db.execute(
        select(CansatData).order_by(CansatData.timestamp)
    ).scalars().all()
    return [format_cansat(r) for r in rows]



