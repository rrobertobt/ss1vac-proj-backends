from pydantic import BaseModel, Field
from datetime import date
from typing import Optional, List
from app.api.routes.users_schemas import RoleInfo


class CreatePayrollPeriodSchema(BaseModel):
    period_start: date = Field(..., description="Start date of the payroll period")
    period_end: date = Field(..., description="End date of the payroll period")


class UpdatePayrollRecordSchema(BaseModel):
    bonuses_amount: Optional[float] = Field(None, ge=0, description="Bonuses amount")
    other_deductions: Optional[float] = Field(None, ge=0, description="Other deductions")


class PayrollPeriodResponseSchema(BaseModel):
    id: int
    period_start: date
    period_end: date
    status: str
    created_at: object
    updated_at: object

    model_config = {
        "from_attributes": True
    }


class PayrollRecordResponseSchema(BaseModel):
    id: int
    employee_id: int
    period_id: int
    base_salary_amount: float
    sessions_count: int
    sessions_amount: float
    bonuses_amount: float
    igss_deduction: float
    other_deductions: float
    total_pay: float
    paid_at: Optional[object]
    created_at: object
    updated_at: object

    model_config = {
        "from_attributes": True
    }


class PayrollUserInfoSchema(BaseModel):
    id: int
    email: str
    username: Optional[str] = None
    role_id: int
    role: Optional[RoleInfo] = None

    model_config = {
        "from_attributes": True
    }


class PayrollEmployeeInfoSchema(BaseModel):
    id: int
    first_name: str
    last_name: str
    user: Optional[PayrollUserInfoSchema] = None

    model_config = {
        "from_attributes": True
    }


class PayrollRecordWithEmployeeSchema(PayrollRecordResponseSchema):
    employee: Optional[PayrollEmployeeInfoSchema] = None

    model_config = {
        "from_attributes": True
    }


class PayrollPeriodRecordsResponseSchema(BaseModel):
    period: PayrollPeriodResponseSchema
    records: List[PayrollRecordWithEmployeeSchema]

    model_config = {
        "from_attributes": True
    }
