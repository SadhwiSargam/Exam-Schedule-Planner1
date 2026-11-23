import datetime
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import engine, Base, get_db, SessionLocal
from schemas import (
    SemesterPlanCreate, SemesterPlanUpdate, SemesterPlanResponse,
    SubjectCreate, SubjectUpdate, SubjectResponse,
    HolidayCreate, HolidayResponse,
    ScheduleConfigCreate, ScheduleConfigUpdate, ScheduleConfigResponse,
    ScheduleEntryCreate, ScheduleEntryUpdate, ScheduleEntryResponse,
    GenerateScheduleRequest, ScheduleValidationResponse, TimetableResponse,
    IATRequest, ValidateEntriesRequest,
)
from database import ExaminationPlan, Subject, Holiday, ScheduleConfiguration, ScheduleEntry
from scheduler.engine import SchedulingEngine
from scheduler.common import parse_time

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Automated Examination Schedule Planner")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://localhost:5176"],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


def get_plan_or_404(db: Session, plan_id: int) -> ExaminationPlan:
    plan = db.query(ExaminationPlan).filter(ExaminationPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(404, "Examination plan not found")
    return plan


@app.get("/")
def health():
    return {"message": "Exam Planner API is running"}


@app.post("/api/plans", response_model=SemesterPlanResponse, status_code=201)
def create_plan(plan: SemesterPlanCreate, db: Session = Depends(get_db)):
    if plan.end_date <= plan.start_date:
        raise HTTPException(400, "Semester end must be after start")
    db_plan = ExaminationPlan(**plan.model_dump())
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)

    default_config = ScheduleConfiguration(plan_id=db_plan.id)
    db.add(default_config)
    db.commit()

    return db_plan


@app.get("/api/plans", response_model=list[SemesterPlanResponse])
def list_plans(db: Session = Depends(get_db)):
    return db.query(ExaminationPlan).order_by(ExaminationPlan.created_at.desc()).all()


@app.get("/api/plans/{plan_id}", response_model=SemesterPlanResponse)
def get_plan(plan_id: int, db: Session = Depends(get_db)):
    return get_plan_or_404(db, plan_id)


@app.put("/api/plans/{plan_id}", response_model=SemesterPlanResponse)
def update_plan(plan_id: int, plan: SemesterPlanUpdate, db: Session = Depends(get_db)):
    db_plan = get_plan_or_404(db, plan_id)
    update_data = plan.model_dump(exclude_unset=True)
    if "end_date" in update_data and "start_date" in update_data:
        if update_data["end_date"] <= update_data["start_date"]:
            raise HTTPException(400, "Semester end must be after start")
    elif "end_date" in update_data:
        if update_data["end_date"] <= db_plan.start_date:
            raise HTTPException(400, "Semester end must be after start")
    elif "start_date" in update_data:
        if db_plan.end_date <= update_data["start_date"]:
            raise HTTPException(400, "Semester end must be after start")

    for key, value in update_data.items():
        setattr(db_plan, key, value)
    db.commit()
    db.refresh(db_plan)
    return db_plan


@app.delete("/api/plans/{plan_id}", status_code=204)
def delete_plan(plan_id: int, db: Session = Depends(get_db)):
    db_plan = get_plan_or_404(db, plan_id)
    db.delete(db_plan)
    db.commit()


@app.post("/api/plans/{plan_id}/subjects", response_model=SubjectResponse, status_code=201)
def create_subject(plan_id: int, subject: SubjectCreate, db: Session = Depends(get_db)):
    get_plan_or_404(db, plan_id)
    existing = db.query(Subject).filter(Subject.plan_id == plan_id, Subject.code == subject.code).first()
    if existing:
        raise HTTPException(400, f"Subject with code '{subject.code}' already exists in this plan")
    db_subject = Subject(plan_id=plan_id, **subject.model_dump())
    db.add(db_subject)
    db.commit()
    db.refresh(db_subject)
    return db_subject


@app.get("/api/plans/{plan_id}/subjects", response_model=list[SubjectResponse])
def list_subjects(plan_id: int, db: Session = Depends(get_db)):
    get_plan_or_404(db, plan_id)
    return db.query(Subject).filter(Subject.plan_id == plan_id).order_by(Subject.code).all()


@app.get("/api/plans/{plan_id}/subjects/{subject_id}", response_model=SubjectResponse)
def get_subject(plan_id: int, subject_id: int, db: Session = Depends(get_db)):
    get_plan_or_404(db, plan_id)
    subject = db.query(Subject).filter(Subject.id == subject_id, Subject.plan_id == plan_id).first()
    if not subject:
        raise HTTPException(404, "Subject not found")
    return subject


@app.put("/api/plans/{plan_id}/subjects/{subject_id}", response_model=SubjectResponse)
def update_subject(plan_id: int, subject_id: int, subject: SubjectUpdate, db: Session = Depends(get_db)):
    get_plan_or_404(db, plan_id)
    db_subject = db.query(Subject).filter(Subject.id == subject_id, Subject.plan_id == plan_id).first()
    if not db_subject:
        raise HTTPException(404, "Subject not found")
    update_data = subject.model_dump(exclude_unset=True)
    if "code" in update_data:
        existing = db.query(Subject).filter(
            Subject.plan_id == plan_id, Subject.code == update_data["code"], Subject.id != subject_id
        ).first()
        if existing:
            raise HTTPException(400, f"Subject with code '{update_data['code']}' already exists")
    for key, value in update_data.items():
        setattr(db_subject, key, value)
    db.commit()
    db.refresh(db_subject)
    return db_subject


@app.delete("/api/plans/{plan_id}/subjects/{subject_id}", status_code=204)
def delete_subject(plan_id: int, subject_id: int, db: Session = Depends(get_db)):
    get_plan_or_404(db, plan_id)
    db_subject = db.query(Subject).filter(Subject.id == subject_id, Subject.plan_id == plan_id).first()
    if not db_subject:
        raise HTTPException(404, "Subject not found")
    db.delete(db_subject)
    db.commit()


@app.post("/api/plans/{plan_id}/holidays", response_model=HolidayResponse, status_code=201)
def create_holiday(plan_id: int, holiday: HolidayCreate, db: Session = Depends(get_db)):
    get_plan_or_404(db, plan_id)
    existing = db.query(Holiday).filter(Holiday.plan_id == plan_id, Holiday.date == holiday.date).first()
    if existing:
        raise HTTPException(400, f"Holiday on {holiday.date} already exists")
    db_holiday = Holiday(plan_id=plan_id, **holiday.model_dump())
    db.add(db_holiday)
    db.commit()
    db.refresh(db_holiday)
    return db_holiday


@app.get("/api/plans/{plan_id}/holidays", response_model=list[HolidayResponse])
def list_holidays(plan_id: int, db: Session = Depends(get_db)):
    get_plan_or_404(db, plan_id)
    return db.query(Holiday).filter(Holiday.plan_id == plan_id).order_by(Holiday.date).all()


@app.delete("/api/plans/{plan_id}/holidays/{holiday_id}", status_code=204)
def delete_holiday(plan_id: int, holiday_id: int, db: Session = Depends(get_db)):
    get_plan_or_404(db, plan_id)
    db_holiday = db.query(Holiday).filter(Holiday.id == holiday_id, Holiday.plan_id == plan_id).first()
    if not db_holiday:
        raise HTTPException(404, "Holiday not found")
    db.delete(db_holiday)
    db.commit()


@app.get("/api/plans/{plan_id}/config", response_model=ScheduleConfigResponse)
def get_config(plan_id: int, db: Session = Depends(get_db)):
    get_plan_or_404(db, plan_id)
    config = db.query(ScheduleConfiguration).filter(ScheduleConfiguration.plan_id == plan_id).first()
    if not config:
        raise HTTPException(404, "Schedule configuration not found")
    return config


@app.put("/api/plans/{plan_id}/config", response_model=ScheduleConfigResponse)
def update_config(plan_id: int, config: ScheduleConfigUpdate, db: Session = Depends(get_db)):
    get_plan_or_404(db, plan_id)
    db_config = db.query(ScheduleConfiguration).filter(ScheduleConfiguration.plan_id == plan_id).first()
    if not db_config:
        raise HTTPException(404, "Schedule configuration not found")
    update_data = config.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_config, key, value)
    db.commit()
    db.refresh(db_config)
    return db_config


@app.post("/api/plans/{plan_id}/schedule/generate", response_model=TimetableResponse)
def generate_schedule(plan_id: int, request: GenerateScheduleRequest, db: Session = Depends(get_db)):
    plan = get_plan_or_404(db, plan_id)

    if request.regenerate:
        db.query(ScheduleEntry).filter(ScheduleEntry.plan_id == plan_id).delete()
        db.commit()

    subjects = db.query(Subject).filter(Subject.plan_id == plan_id).all()
    if not subjects:
        raise HTTPException(400, "No subjects configured for this plan")

    holidays = db.query(Holiday).filter(Holiday.plan_id == plan_id).all()
    holiday_dates = [h.date for h in holidays]

    config = db.query(ScheduleConfiguration).filter(ScheduleConfiguration.plan_id == plan_id).first()
    if not config:
        raise HTTPException(400, "Schedule configuration not found")

    engine = SchedulingEngine(config, set(holiday_dates))
    entries, validation = engine.generate_full_schedule(subjects)

    for entry_data in entries:
        subject = next(s for s in subjects if s.code == entry_data["subject_code"])
        db_entry = ScheduleEntry(
            plan_id=plan_id,
            subject_id=subject.id,
            assessment_type=entry_data["exam_type"],
            date=datetime.date.fromisoformat(entry_data["date"]),
            start_time=entry_data["start"],
            end_time=entry_data["end"],
            batch_number=entry_data["batch_number"],
        )
        db.add(db_entry)
    db.commit()

    db_entries = db.query(ScheduleEntry).filter(ScheduleEntry.plan_id == plan_id).all()
    response_entries = []
    for e in db_entries:
        subj = db.query(Subject).filter(Subject.id == e.subject_id).first()
        response_entries.append(ScheduleEntryResponse(
            **e.__dict__,
            subject_code=subj.code if subj else None,
            subject_name=subj.name if subj else None,
        ))

    return TimetableResponse(
        plan_id=plan.id,
        plan_title=plan.title,
        semester=plan.semester,
        academic_year=plan.academic_year,
        entries=response_entries,
        validation=ScheduleValidationResponse(**validation)
    )


@app.get("/api/plans/{plan_id}/schedule", response_model=TimetableResponse)
def get_schedule(plan_id: int, db: Session = Depends(get_db)):
    plan = get_plan_or_404(db, plan_id)
    db_entries = db.query(ScheduleEntry).filter(ScheduleEntry.plan_id == plan_id).all()

    subjects = db.query(Subject).filter(Subject.plan_id == plan_id).all()
    holidays = [h.date for h in db.query(Holiday).filter(Holiday.plan_id == plan_id).all()]
    config = db.query(ScheduleConfiguration).filter(ScheduleConfiguration.plan_id == plan_id).first()

    response_entries = []
    for e in db_entries:
        subj = next((s for s in subjects if s.id == e.subject_id), None)
        response_entries.append(ScheduleEntryResponse(
            **e.__dict__,
            subject_code=subj.code if subj else None,
            subject_name=subj.name if subj else None,
        ))

    validation = {"valid": True, "conflicts": [], "unscheduled": [], "warnings": []}
    if config:
        engine = SchedulingEngine(config, set(holidays))
        validation["conflicts"] = engine.validate_all(
            [e.__dict__ for e in db_entries], subjects
        )
        validation["valid"] = len(validation["conflicts"]) == 0

    return TimetableResponse(
        plan_id=plan.id,
        plan_title=plan.title,
        semester=plan.semester,
        academic_year=plan.academic_year,
        entries=response_entries,
        validation=ScheduleValidationResponse(**validation)
    )


@app.post("/api/plans/{plan_id}/schedule/validate", response_model=ScheduleValidationResponse)
def validate_schedule(plan_id: int, db: Session = Depends(get_db)):
    plan = get_plan_or_404(db, plan_id)
    db_entries = db.query(ScheduleEntry).filter(ScheduleEntry.plan_id == plan_id).all()
    subjects = db.query(Subject).filter(Subject.plan_id == plan_id).all()
    holidays = [h.date for h in db.query(Holiday).filter(Holiday.plan_id == plan_id).all()]
    config = db.query(ScheduleConfiguration).filter(ScheduleConfiguration.plan_id == plan_id).first()

    if not config:
        return ScheduleValidationResponse(valid=False, conflicts=["No schedule configuration"], unscheduled=[], warnings=[])

    engine = SchedulingEngine(config, set(holidays))
    conflicts = engine.validate_all([e.__dict__ for e in db_entries], subjects)

    return ScheduleValidationResponse(
        valid=len(conflicts) == 0,
        conflicts=conflicts,
        unscheduled=[],
        warnings=[]
    )


@app.post("/api/plans/{plan_id}/schedule/validate-entries", response_model=ScheduleValidationResponse)
def validate_schedule_entries(plan_id: int, request: ValidateEntriesRequest, db: Session = Depends(get_db)):
    plan = get_plan_or_404(db, plan_id)
    subjects = db.query(Subject).filter(Subject.plan_id == plan_id).all()
    holidays = [h.date for h in db.query(Holiday).filter(Holiday.plan_id == plan_id).all()]
    config = db.query(ScheduleConfiguration).filter(ScheduleConfiguration.plan_id == plan_id).first()

    if not config:
        return ScheduleValidationResponse(valid=False, conflicts=["No schedule configuration"], unscheduled=[], warnings=[])

    engine = SchedulingEngine(config, set(holidays))
    conflicts = engine.validate_all(request.entries, subjects)

    return ScheduleValidationResponse(
        valid=len(conflicts) == 0,
        conflicts=conflicts,
        unscheduled=[],
        warnings=[]
    )


@app.put("/api/plans/{plan_id}/schedule/entries/{entry_id}", response_model=ScheduleEntryResponse)
def update_schedule_entry(plan_id: int, entry_id: int, entry: ScheduleEntryUpdate, db: Session = Depends(get_db)):
    get_plan_or_404(db, plan_id)
    db_entry = db.query(ScheduleEntry).filter(ScheduleEntry.id == entry_id, ScheduleEntry.plan_id == plan_id).first()
    if not db_entry:
        raise HTTPException(404, "Schedule entry not found")

    update_data = entry.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_entry, key, value)
    db_entry.status = "manual"
    db.commit()
    db.refresh(db_entry)

    subj = db.query(Subject).filter(Subject.id == db_entry.subject_id).first()
    return ScheduleEntryResponse(
        **db_entry.__dict__,
        subject_code=subj.code if subj else None,
        subject_name=subj.name if subj else None,
    )


@app.delete("/api/plans/{plan_id}/schedule/entries/{entry_id}", status_code=204)
def delete_schedule_entry(plan_id: int, entry_id: int, db: Session = Depends(get_db)):
    get_plan_or_404(db, plan_id)
    db_entry = db.query(ScheduleEntry).filter(ScheduleEntry.id == entry_id, ScheduleEntry.plan_id == plan_id).first()
    if not db_entry:
        raise HTTPException(404, "Schedule entry not found")
    db.delete(db_entry)
    db.commit()


@app.post("/api/timetable/iat")
def create_iat(request: IATRequest):
    if request.end_date < request.start_date:
        raise HTTPException(400, "Scheduling range is invalid.")
    try:
        result = generate_iat(
            request.subjects, request.start_date, request.end_date,
            set(request.holidays), request.iat_number
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    return {"iat_number": request.iat_number, "schedule": result}


@app.post("/api/subjects/order")
def order_subjects(subjects: list[SubjectResponse]):
    from scheduler.common import ordered_subjects
    ordered = ordered_subjects(subjects)
    return [s.model_dump() for s in ordered]


@app.get("/api/plans/{plan_id}/schedule/export/pdf")
def export_pdf(plan_id: int, db: Session = Depends(get_db)):
    plan = get_plan_or_404(db, plan_id)
    db_entries = db.query(ScheduleEntry).filter(ScheduleEntry.plan_id == plan_id).all()
    subjects = {s.id: s for s in db.query(Subject).filter(Subject.plan_id == plan_id).all()}

    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from io import BytesIO

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), leftMargin=15*mm, rightMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Title'], fontSize=16, alignment=TA_CENTER, spaceAfter=6)
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER, spaceAfter=12)
    header_style = ParagraphStyle('Header', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER, fontName='Helvetica-Bold')

    elements = []
    elements.append(Paragraph(plan.title, title_style))
    elements.append(Paragraph(f"Semester {plan.semester} &nbsp; | &nbsp; Academic Year: {plan.academic_year} &nbsp; | &nbsp; {plan.start_date} to {plan.end_date}", subtitle_style))
    elements.append(Spacer(1, 8))

    headers = ["Date", "Day", "Exam Type", "Subject Code", "Subject Name", "Batch", "Start", "End", "Status"]
    data = [headers]

    for e in sorted(db_entries, key=lambda x: (x.date, x.start_time)):
        subj = subjects.get(e.subject_id)
        d = datetime.datetime.strptime(str(e.date), "%Y-%m-%d")
        day = d.strftime("%a")
        batch = str(e.batch_number) if e.batch_number > 1 else "-"
        data.append([
            str(e.date), day, e.assessment_type,
            subj.code if subj else "", subj.name if subj else "",
            batch, e.start_time, e.end_time, e.status
        ])

    col_widths = [22*mm, 15*mm, 25*mm, 22*mm, 55*mm, 12*mm, 18*mm, 18*mm, 18*mm]
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#263b75')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e1e7ef')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))

    elements.append(table)
    doc.build(elements)
    buffer.seek(0)

    from fastapi.responses import StreamingResponse
    return StreamingResponse(buffer, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="timetable-{plan_id}.pdf"'})