from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import BigInteger, String, Boolean, TIMESTAMP, ForeignKey, func, Integer, Text, Table, Column, Numeric, Date, SmallInteger, Time

class Base(DeclarativeBase):
    pass

# Tabla de asociación para la relación many-to-many entre roles y permisos
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", BigInteger, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", BigInteger, ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now(), nullable=False),
)

class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    code: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relación many-to-many con Permission
    permissions: Mapped[list["Permission"]] = relationship(
        "Permission",
        secondary=role_permissions,
        lazy="joined"
    )

class Area(Base):
    __tablename__ = "areas"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class Specialty(Base):
    __tablename__ = "specialties"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

# Tabla de asociación para employee_specialties
employee_specialties = Table(
    "employee_specialties",
    Base.metadata,
    Column("employee_id", BigInteger, ForeignKey("employees.id", ondelete="CASCADE"), primary_key=True),
    Column("specialty_id", BigInteger, ForeignKey("specialties.id", ondelete="CASCADE"), primary_key=True),
)

class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), unique=True, nullable=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    license_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    area_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("areas.id", ondelete="SET NULL"), nullable=True)
    base_salary: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    session_rate: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    igss_percentage: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    hired_at: Mapped[object | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")
    created_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relación con User
    user: Mapped["User"] = relationship("User", lazy="joined", foreign_keys=[user_id])
    
    # Relación con Area
    area: Mapped["Area"] = relationship("Area", lazy="joined", foreign_keys=[area_id])
    
    # Relación con Specialties (many-to-many)
    specialties: Mapped[list["Specialty"]] = relationship(
        "Specialty",
        secondary=employee_specialties,
        lazy="joined"
    )
    
    # Relación con Availability (one-to-many)
    availability: Mapped[list["EmployeeAvailability"]] = relationship(
        "EmployeeAvailability",
        lazy="joined",
        foreign_keys="EmployeeAvailability.employee_id",
        overlaps="employee"
    )
    
    # Relación con PayrollRecord (one-to-many)
    payroll_records: Mapped[list["PayrollRecord"]] = relationship(
        "PayrollRecord",
        back_populates="employee"
    )

class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), unique=True, nullable=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    dob: Mapped[object | None] = mapped_column(Date, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    marital_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    occupation: Mapped[str | None] = mapped_column(String(120), nullable=True)
    education_level: Mapped[str | None] = mapped_column(String(120), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    emergency_contact_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    emergency_contact_relationship: Mapped[str | None] = mapped_column(String(80), nullable=True)
    emergency_contact_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")
    created_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class ClinicalRecord(Base):
    __tablename__ = "clinical_records"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    patient_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    record_number: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True)
    institution_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    service: Mapped[str | None] = mapped_column(String(120), nullable=True)
    opening_date: Mapped[object | None] = mapped_column(Date, nullable=True)
    responsible_employee_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("employees.id", ondelete="SET NULL"), nullable=True)
    responsible_license: Mapped[str | None] = mapped_column(String(100), nullable=True)
    referral_source: Mapped[str | None] = mapped_column(String(150), nullable=True)
    chief_complaint: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")
    created_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones
    patient: Mapped["Patient"] = relationship("Patient", lazy="joined")
    responsible_employee: Mapped["Employee"] = relationship("Employee", lazy="joined", foreign_keys=[responsible_employee_id])

class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    area_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("areas.id", ondelete="SET NULL"), nullable=True)
    default_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class EmployeeAvailability(Base):
    __tablename__ = "employee_availability"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    day_of_week: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    start_time: Mapped[object] = mapped_column(Time, nullable=False)
    end_time: Mapped[object] = mapped_column(Time, nullable=False)
    specialty_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("specialties.id", ondelete="SET NULL"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones
    employee: Mapped["Employee"] = relationship("Employee", lazy="joined")
    specialty: Mapped["Specialty"] = relationship("Specialty", lazy="joined")

class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    patient_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    professional_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("employees.id", ondelete="SET NULL"), nullable=True)
    specialty_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("specialties.id", ondelete="SET NULL"), nullable=True)
    appointment_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    start_datetime: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    end_datetime: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="SCHEDULED")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones
    patient: Mapped["Patient"] = relationship("Patient", lazy="joined")
    professional: Mapped["Employee"] = relationship("Employee", lazy="joined", foreign_keys=[professional_id])
    specialty: Mapped["Specialty"] = relationship("Specialty", lazy="joined")

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)

    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("roles.id"), nullable=False)

    # Relaciones
    role: Mapped["Role"] = relationship("Role", lazy="joined")
    employee: Mapped["Employee"] = relationship("Employee", uselist=False, lazy="joined", overlaps="user")
    patient: Mapped["Patient"] = relationship("Patient", uselist=False, lazy="joined")

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    two_fa_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    two_fa_secret: Mapped[str | None] = mapped_column(String(255), nullable=True)
    two_fa_expires_at: Mapped[object | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    two_fa_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    password_reset_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    password_reset_expires: Mapped[object | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    last_login_at: Mapped[object | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    created_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class PatientTask(Base):
    __tablename__ = "patient_tasks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    patient_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    clinical_record_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("clinical_records.id", ondelete="SET NULL"), nullable=True)
    assigned_by_employee_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("employees.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_date: Mapped[object | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")
    created_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones
    patient: Mapped["Patient"] = relationship("Patient", lazy="joined")
    clinical_record: Mapped["ClinicalRecord"] = relationship("ClinicalRecord", lazy="joined")
    assigned_by: Mapped["Employee"] = relationship("Employee", lazy="joined", foreign_keys=[assigned_by_employee_id])


class ConfidentialNote(Base):
    __tablename__ = "confidential_notes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    patient_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    clinical_record_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("clinical_records.id", ondelete="CASCADE"), nullable=False)
    author_employee_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("employees.id", ondelete="SET NULL"), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    # Relaciones
    patient: Mapped["Patient"] = relationship("Patient", lazy="joined")
    clinical_record: Mapped["ClinicalRecord"] = relationship("ClinicalRecord", lazy="joined")
    author: Mapped["Employee"] = relationship("Employee", lazy="joined", foreign_keys=[author_employee_id])


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    clinical_record_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("clinical_records.id", ondelete="CASCADE"), nullable=False)
    professional_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("employees.id", ondelete="SET NULL"), nullable=True)
    session_datetime: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    session_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    attended: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    absence_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    topics: Mapped[str | None] = mapped_column(Text, nullable=True)
    interventions: Mapped[str | None] = mapped_column(Text, nullable=True)
    patient_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    assigned_tasks: Mapped[str | None] = mapped_column(Text, nullable=True)
    observations: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_appointment_datetime: Mapped[object | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    digital_signature_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    appointment_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("appointments.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones
    clinical_record: Mapped["ClinicalRecord"] = relationship("ClinicalRecord", lazy="joined")
    professional: Mapped["Employee"] = relationship("Employee", lazy="joined", foreign_keys=[professional_id])


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    sku: Mapped[str | None] = mapped_column(String(80), unique=True, nullable=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    product_type: Mapped[str] = mapped_column(String(30), nullable=False, default="OTHER")
    unit: Mapped[str | None] = mapped_column(String(30), nullable=True)
    cost_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    sale_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    min_stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class PaymentMethod(Base):
    __tablename__ = "payment_methods"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    created_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    invoice_number: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    patient_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("patients.id", ondelete="RESTRICT"), nullable=False)
    created_by_employee_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("employees.id", ondelete="SET NULL"), nullable=True)
    invoice_date: Mapped[object] = mapped_column(Date, nullable=False, server_default=func.current_date())
    due_date: Mapped[object | None] = mapped_column(Date, nullable=True)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="GTQ")
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ISSUED")
    pdf_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones
    patient: Mapped["Patient"] = relationship("Patient", lazy="joined")
    created_by: Mapped["Employee"] = relationship("Employee", lazy="joined", foreign_keys=[created_by_employee_id])
    items: Mapped[list["InvoiceItem"]] = relationship("InvoiceItem", lazy="joined", foreign_keys="InvoiceItem.invoice_id")
    payments: Mapped[list["Payment"]] = relationship("Payment", lazy="joined", foreign_keys="Payment.invoice_id")


class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    invoice_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    service_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("services.id", ondelete="SET NULL"), nullable=True)
    product_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    quantity: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=1)
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    created_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    # Relaciones
    invoice: Mapped["Invoice"] = relationship("Invoice", lazy="joined", overlaps="items")
    service: Mapped["Service"] = relationship("Service", lazy="joined")
    product: Mapped["Product"] = relationship("Product", lazy="joined")


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    invoice_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    payment_method_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("payment_methods.id", ondelete="SET NULL"), nullable=True)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    paid_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    reference: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    # Relaciones
    invoice: Mapped["Invoice"] = relationship("Invoice", lazy="joined", overlaps="payments")
    payment_method: Mapped["PaymentMethod"] = relationship("PaymentMethod", lazy="joined")


class PayrollPeriod(Base):
    __tablename__ = "payroll_periods"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    period_start: Mapped[object] = mapped_column(Date, nullable=False)
    period_end: Mapped[object] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="OPEN")
    created_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones
    records: Mapped[list["PayrollRecord"]] = relationship("PayrollRecord", back_populates="period", foreign_keys="PayrollRecord.period_id")


class PayrollRecord(Base):
    __tablename__ = "payroll_records"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    employee_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False)
    period_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("payroll_periods.id", ondelete="RESTRICT"), nullable=False)
    base_salary_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    sessions_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sessions_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    bonuses_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    igss_deduction: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    other_deductions: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    total_pay: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    paid_at: Mapped[object | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones
    employee: Mapped["Employee"] = relationship("Employee", back_populates="payroll_records")
    period: Mapped["PayrollPeriod"] = relationship("PayrollPeriod", back_populates="records")

