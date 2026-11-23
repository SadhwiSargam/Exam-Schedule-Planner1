import os
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Date, DateTime, Boolean,
    ForeignKey, Text, Enum as SQLEnum, UniqueConstraint
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./exam_planner.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


class ExaminationPlan(Base):
    __tablename__ = "examination_plans"

    id = Column(Integer, primary_key=True, index=True)
    semester = Column(Integer, nullable=False)
    academic_year = Column(String(20), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    subjects = relationship("Subject", back_populates="plan", cascade="all, delete-orphan")
    holidays = relationship("Holiday", back_populates="plan", cascade="all, delete-orphan")
    schedule_config = relationship("ScheduleConfiguration", back_populates="plan", uselist=False, cascade="all, delete-orphan")
    schedule_entries = relationship("ScheduleEntry", back_populates="plan", cascade="all, delete-orphan")


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("examination_plans.id", ondelete="CASCADE"), nullable=False)
    code = Column(String(20), nullable=False)
    name = Column(String(200), nullable=False)
    category = Column(SQLEnum("theory", "practical", "both", name="subject_category"), nullable=False)
    internal_count = Column(Integer, default=3)
    internal_duration_minutes = Column(Integer, default=90)
    see_duration_minutes = Column(Integer, default=180)
    lab_internal_duration_minutes = Column(Integer, default=120)
    lab_external_duration_minutes = Column(Integer, default=180)
    mathematics_related = Column(Boolean, default=False)
    num_batches = Column(Integer, default=1)

    plan = relationship("ExaminationPlan", back_populates="subjects")
    schedule_entries = relationship("ScheduleEntry", back_populates="subject", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("plan_id", "code", name="uq_plan_subject_code"),)


class Holiday(Base):
    __tablename__ = "holidays"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("examination_plans.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    plan = relationship("ExaminationPlan", back_populates="holidays")

    __table_args__ = (UniqueConstraint("plan_id", "date", name="uq_plan_holiday_date"),)


class ScheduleConfiguration(Base):
    __tablename__ = "schedule_configurations"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("examination_plans.id", ondelete="CASCADE"), nullable=False, unique=True)

    iat1_start = Column(Date, nullable=True)
    iat1_end = Column(Date, nullable=True)
    iat2_start = Column(Date, nullable=True)
    iat2_end = Column(Date, nullable=True)
    iat3_start = Column(Date, nullable=True)
    iat3_end = Column(Date, nullable=True)

    iat_morning_start = Column(String(5), default="09:30")
    iat_morning_end = Column(String(5), default="11:00")
    iat_afternoon_start = Column(String(5), default="14:30")
    iat_afternoon_end = Column(String(5), default="16:00")

    lab_internal_start = Column(Date, nullable=True)
    lab_internal_end = Column(Date, nullable=True)
    lab_external_start = Column(Date, nullable=True)
    lab_external_end = Column(Date, nullable=True)
    max_lab_batches_per_day = Column(Integer, default=2)

    see_start = Column(Date, nullable=True)
    see_end = Column(Date, nullable=True)
    see_gap_days = Column(Integer, default=1)

    weekend_exclude_saturday = Column(Boolean, default=True)
    weekend_exclude_sunday = Column(Boolean, default=True)

    plan = relationship("ExaminationPlan", back_populates="schedule_config")


class ScheduleEntry(Base):
    __tablename__ = "schedule_entries"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("examination_plans.id", ondelete="CASCADE"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)

    assessment_type = Column(String(50), nullable=False)
    date = Column(Date, nullable=False)
    start_time = Column(String(5), nullable=False)
    end_time = Column(String(5), nullable=False)
    batch_number = Column(Integer, default=1)
    status = Column(String(20), default="scheduled")

    plan = relationship("ExaminationPlan", back_populates="schedule_entries")
    subject = relationship("Subject", back_populates="schedule_entries")

    __table_args__ = (UniqueConstraint("plan_id", "subject_id", "assessment_type", "date", "batch_number", name="uq_schedule_entry"),)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()