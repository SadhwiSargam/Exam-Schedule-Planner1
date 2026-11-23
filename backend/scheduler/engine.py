from datetime import date, timedelta
from typing import Protocol
from .types import SubjectProtocol, ScheduleConfigProtocol
from .common import parse_time
from .iat import schedule_iat, validate_iat_schedule
from .lab_internal import schedule_lab_internal, validate_lab_internal_schedule, validate_no_theory_lab_internal
from .lab_external import schedule_lab_external, validate_lab_external_schedule, validate_no_theory_lab_external
from .see import schedule_see, validate_see_schedule


class SchedulingEngine:
    def __init__(self, config: ScheduleConfigProtocol, holidays: set[date]):
        self.config = config
        self.holidays = holidays
        self.exclude_saturday = config.weekend_exclude_saturday
        self.exclude_sunday = config.weekend_exclude_sunday

    def generate_full_schedule(self, subjects: list[SubjectProtocol]) -> tuple[list[dict], dict]:
        """Generate complete examination schedule.

        Returns (schedule_entries, validation_results)
        """
        all_entries = []
        validation = {
            "valid": True,
            "conflicts": [],
            "unscheduled": [],
            "warnings": [],
        }

        for iat_num in [1, 2, 3]:
            iat_start = getattr(self.config, f"iat{iat_num}_start")
            iat_end = getattr(self.config, f"iat{iat_num}_end")
            if iat_start and iat_end:
                try:
                    entries = schedule_iat(
                        subjects, iat_start, iat_end, self.holidays, iat_num,
                        self.config.iat_morning_start, self.config.iat_morning_end,
                        self.config.iat_afternoon_start, self.config.iat_afternoon_end,
                        self.exclude_saturday, self.exclude_sunday
                    )
                    all_entries.extend(entries)
                except ValueError as e:
                    validation["unscheduled"].append(f"IAT {iat_num}: {e}")
            else:
                validation["warnings"].append(f"IAT {iat_num}: date window not configured")

        lab_int_start = self.config.lab_internal_start
        lab_int_end = self.config.lab_internal_end
        validation["conflicts"].extend(validate_no_theory_lab_internal(subjects))
        if lab_int_start and lab_int_end:
            try:
                entries = schedule_lab_internal(
                    subjects, lab_int_start, lab_int_end, self.holidays,
                    lab_internal_duration_minutes=120,
                    max_batches_per_day=self.config.max_lab_batches_per_day,
                    exclude_saturday=self.exclude_saturday,
                    exclude_sunday=self.exclude_sunday
                )
                all_entries.extend(entries)
            except ValueError as e:
                validation["unscheduled"].append(f"Lab Internal: {e}")
        else:
            validation["warnings"].append("Lab Internal: date window not configured")

        lab_ext_start = self.config.lab_external_start
        lab_ext_end = self.config.lab_external_end
        iat3_end = self.config.iat3_end
        validation["conflicts"].extend(validate_no_theory_lab_external(subjects))
        if lab_ext_start and lab_ext_end:
            try:
                entries = schedule_lab_external(
                    subjects, lab_ext_start, lab_ext_end, self.holidays,
                    iat3_end_date=iat3_end,
                    lab_external_duration_minutes=180,
                    max_batches_per_day=self.config.max_lab_batches_per_day,
                    exclude_saturday=self.exclude_saturday,
                    exclude_sunday=self.exclude_sunday
                )
                all_entries.extend(entries)
            except ValueError as e:
                validation["unscheduled"].append(f"Lab External: {e}")
        else:
            validation["warnings"].append("Lab External: date window not configured")

        see_start = self.config.see_start
        see_end = self.config.see_end
        if see_start and see_end:
            try:
                entries = schedule_see(
                    subjects, see_start, see_end, self.holidays,
                    see_duration_minutes=180,
                    gap_days=self.config.see_gap_days,
                    exclude_saturday=self.exclude_saturday,
                    exclude_sunday=self.exclude_sunday
                )
                all_entries.extend(entries)
            except ValueError as e:
                validation["unscheduled"].append(f"SEE: {e}")
        else:
            validation["warnings"].append("SEE: date window not configured")

        validation["conflicts"] = self.validate_all(all_entries, subjects)
        validation["valid"] = len(validation["conflicts"]) == 0 and len(validation["unscheduled"]) == 0

        return all_entries, validation

    def validate_all(self, entries: list[dict], subjects: list[SubjectProtocol]) -> list[str]:
        """Validate entire schedule and return conflicts."""
        all_errors = []

        iat_entries = [e for e in entries if e["exam_type"].startswith("IAT")]
        for iat_num in [1, 2, 3]:
            start = getattr(self.config, f"iat{iat_num}_start")
            end = getattr(self.config, f"iat{iat_num}_end")
            if start and end:
                iat_sched = [e for e in iat_entries if e["exam_type"] == f"IAT {iat_num}"]
                errors = validate_iat_schedule(
                    iat_sched, subjects, start, end, self.holidays, iat_num,
                    self.exclude_saturday, self.exclude_sunday
                )
                all_errors.extend(errors)

        lab_int_start = self.config.lab_internal_start
        lab_int_end = self.config.lab_internal_end
        if lab_int_start and lab_int_end:
            lab_int_sched = [e for e in entries if e["exam_type"] == "Lab Internal"]
            errors = validate_lab_internal_schedule(
                lab_int_sched, subjects, lab_int_start, lab_int_end, self.holidays,
                self.config.max_lab_batches_per_day,
                self.exclude_saturday, self.exclude_sunday
            )
            all_errors.extend(errors)

        lab_ext_start = self.config.lab_external_start
        lab_ext_end = self.config.lab_external_end
        if lab_ext_start and lab_ext_end:
            lab_ext_sched = [e for e in entries if e["exam_type"] == "Lab External"]
            errors = validate_lab_external_schedule(
                lab_ext_sched, subjects, lab_ext_start, lab_ext_end, self.holidays,
                iat3_end_date=self.config.iat3_end,
                max_batches_per_day=self.config.max_lab_batches_per_day,
                exclude_saturday=self.exclude_saturday,
                exclude_sunday=self.exclude_sunday
            )
            all_errors.extend(errors)

        see_start = self.config.see_start
        see_end = self.config.see_end
        if see_start and see_end:
            see_sched = [e for e in entries if e["exam_type"] == "SEE"]
            errors = validate_see_schedule(
                see_sched, subjects, see_start, see_end, self.holidays,
                self.config.see_gap_days,
                self.exclude_saturday, self.exclude_sunday
            )
            all_errors.extend(errors)

        all_errors.extend(self._check_cross_conflicts(entries))

        return all_errors

    def _check_cross_conflicts(self, entries: list[dict]) -> list[str]:
        """Check for conflicts across different exam types on same day/time."""
        errors = []
        by_day_time = {}

        for entry in entries:
            key = (entry["date"], entry["start"], entry["end"])
            if key not in by_day_time:
                by_day_time[key] = []
            by_day_time[key].append(entry)

        for (day, start, end), exams in by_day_time.items():
            if len(exams) > 1:
                exam_strs = [f"{e['exam_type']}({e['subject_code']})" for e in exams]
                errors.append(f"Time conflict on {day} {start}-{end}: {', '.join(exam_strs)}")

        return errors


def generate_schedule(
    subjects: list[SubjectProtocol],
    config: ScheduleConfigProtocol,
    holidays: list[date],
) -> tuple[list[dict], dict]:
    """Convenience function to generate schedule."""
    engine = SchedulingEngine(config, set(holidays))
    return engine.generate_full_schedule(subjects)


def validate_schedule(
    entries: list[dict],
    subjects: list[SubjectProtocol],
    config: ScheduleConfigProtocol,
    holidays: list[date],
) -> dict:
    """Validate an existing schedule."""
    engine = SchedulingEngine(config, set(holidays))
    conflicts = engine.validate_all(entries, subjects)
    return {
        "valid": len(conflicts) == 0,
        "conflicts": conflicts,
        "unscheduled": [],
        "warnings": [],
    }