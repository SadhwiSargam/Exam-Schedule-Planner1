import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field, ConfigDict

Category = Literal["theory", "practical", "both"]
AssessmentType = Literal["IAT 1", "IAT 2", "IAT 3", "Lab Internal", "Lab External", "SEE"]
EntryStatus = Literal["scheduled", "manual", "conflict", "cancelled"]


class SemesterPlanBase(BaseModel):
    semester: int = Field(ge=3, le=8)
    academic_year: str = Field(min_length=4, max_length=20)
    start_date: datetime.date
    end_date: datetime.date
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None


class SemesterPlanCreate(SemesterPlanBase):
    pass


class SemesterPlanUpdate(BaseModel):
    semester: Optional[int] = Field(default=None, ge=3, le=8)
    academic_year: Optional[str] = Field(default=None, min_length=4, max_length=20)
    start_date: Optional[datetime.date] = None
    end_date: Optional[datetime.date] = None
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None


class SemesterPlanResponse(SemesterPlanBase):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class SubjectBase(BaseModel):
    code: str = Field(min_length=1, max_length=20)
    name: str = Field(min_length=1, max_length=200)
    category: Category
    internal_count: int = Field(default=3, ge=0, le=3)
    internal_duration_minutes: int = Field(default=90, gt=0)
    see_duration_minutes: int = Field(default=180, gt=0)
    lab_internal_duration_minutes: int = Field(default=120, gt=0)
    lab_external_duration_minutes: int = Field(default=180, gt=0)
    mathematics_related: bool = False
    num_batches: int = Field(default=1, ge=1)


class SubjectCreate(SubjectBase):
    pass


class SubjectUpdate(BaseModel):
    code: Optional[str] = Field(default=None, min_length=1, max_length=20)
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    category: Optional[Category] = None
    internal_count: Optional[int] = Field(default=None, ge=0, le=3)
    internal_duration_minutes: Optional[int] = Field(default=None, gt=0)
    see_duration_minutes: Optional[int] = Field(default=None, gt=0)
    lab_internal_duration_minutes: Optional[int] = Field(default=None, gt=0)
    lab_external_duration_minutes: Optional[int] = Field(default=None, gt=0)
    mathematics_related: Optional[bool] = None
    num_batches: Optional[int] = Field(default=None, ge=1)


class SubjectResponse(SubjectBase):
    id: int
    plan_id: int

    model_config = ConfigDict(from_attributes=True)


class HolidayBase(BaseModel):
    date: datetime.date
    name: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None


class HolidayCreate(HolidayBase):
    pass


class HolidayResponse(HolidayBase):
    id: int
    plan_id: int

    model_config = ConfigDict(from_attributes=True)


class ScheduleConfigBase(BaseModel):
    iat1_start: Optional[datetime.date] = None
    iat1_end: Optional[datetime.date] = None
    iat2_start: Optional[datetime.date] = None
    iat2_end: Optional[datetime.date] = None
    iat3_start: Optional[datetime.date] = None
    iat3_end: Optional[datetime.date] = None

    iat_morning_start: str = "09:30"
    iat_morning_end: str = "11:00"
    iat_afternoon_start: str = "14:30"
    iat_afternoon_end: str = "16:00"

    lab_internal_start: Optional[datetime.date] = None
    lab_internal_end: Optional[datetime.date] = None
    lab_external_start: Optional[datetime.date] = None
    lab_external_end: Optional[datetime.date] = None
    max_lab_batches_per_day: int = Field(default=2, ge=1)

    see_start: Optional[datetime.date] = None
    see_end: Optional[datetime.date] = None
    see_gap_days: int = Field(default=1, ge=0)

    weekend_exclude_saturday: bool = True
    weekend_exclude_sunday: bool = True


class ScheduleConfigCreate(ScheduleConfigBase):
    pass


class ScheduleConfigUpdate(BaseModel):
    iat1_start: Optional[datetime.date] = None
    iat1_end: Optional[datetime.date] = None
    iat2_start: Optional[datetime.date] = None
    iat2_end: Optional[datetime.date] = None
    iat3_start: Optional[datetime.date] = None
    iat3_end: Optional[datetime.date] = None

    iat_morning_start: Optional[str] = None
    iat_morning_end: Optional[str] = None
    iat_afternoon_start: Optional[str] = None
    iat_afternoon_end: Optional[str] = None

    lab_internal_start: Optional[datetime.date] = None
    lab_internal_end: Optional[datetime.date] = None
    lab_external_start: Optional[datetime.date] = None
    lab_external_end: Optional[datetime.date] = None
    max_lab_batches_per_day: Optional[int] = Field(default=None, ge=1)

    see_start: Optional[datetime.date] = None
    see_end: Optional[datetime.date] = None
    see_gap_days: Optional[int] = Field(default=None, ge=0)

    weekend_exclude_saturday: Optional[bool] = None
    weekend_exclude_sunday: Optional[bool] = None


class ScheduleConfigResponse(ScheduleConfigBase):
    id: int
    plan_id: int

    model_config = ConfigDict(from_attributes=True)


class ScheduleEntryBase(BaseModel):
    subject_id: int
    assessment_type: AssessmentType
    date: datetime.date
    start_time: str
    end_time: str
    batch_number: int = 1
    status: EntryStatus = "scheduled"


class ScheduleEntryCreate(ScheduleEntryBase):
    pass


class ScheduleEntryUpdate(BaseModel):
    subject_id: Optional[int] = None
    assessment_type: Optional[AssessmentType] = None
    date: Optional[datetime.date] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    batch_number: Optional[int] = None
    status: Optional[EntryStatus] = None


class ScheduleEntryResponse(ScheduleEntryBase):
    id: int
    plan_id: int
    subject_code: Optional[str] = None
    subject_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class IATRequest(BaseModel):
    subjects: list[SubjectBase]
    start_date: datetime.date
    end_date: datetime.date
    holidays: list[datetime.date] = []
    iat_number: int = Field(ge=1, le=3)


class GenerateScheduleRequest(BaseModel):
    plan_id: int
    regenerate: bool = False


class ValidateEntriesRequest(BaseModel):
    entries: list[dict]


class ScheduleValidationResponse(BaseModel):
    valid: bool
    conflicts: list[str] = []
    unscheduled: list[str] = []
    warnings: list[str] = []


class TimetableResponse(BaseModel):
    plan_id: int
    plan_title: str
    semester: int
    academic_year: str
    entries: list[ScheduleEntryResponse]
    validation: ScheduleValidationResponse