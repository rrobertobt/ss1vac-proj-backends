from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional


class ReportPeriodSchema(BaseModel):
    start_date: date
    end_date: date


class RevenueReportSchema(ReportPeriodSchema):
    currency: Optional[str] = "GTQ"


class PayrollReportSchema(ReportPeriodSchema):
    employee_id: Optional[int] = None


class SalesHistorySchema(ReportPeriodSchema):
    patient_id: Optional[int] = None


class PatientsPerSpecialtySchema(ReportPeriodSchema):
    specialty_id: Optional[int] = None
    area_id: Optional[int] = None
