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
        foreign_keys="EmployeeAvailability.employee_id"
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
    employee: Mapped["Employee"] = relationship("Employee", uselist=False, lazy="joined")
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
