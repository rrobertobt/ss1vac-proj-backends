-- ==========================================
-- PsiFirm - PostgreSQL DDL
-- ==========================================
-- Recomendado: ejecutar en una base vacía
-- ==========================================
BEGIN;

-- -----------------------------
-- Utilidades
-- -----------------------------
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================
-- 1) Seguridad: Roles y Permisos
-- =============================
CREATE TABLE roles (
  id SERIAL PRIMARY KEY,
  name VARCHAR(50) UNIQUE NOT NULL,
  -- SUPER_ADMIN, PSYCHOLOGIST, ADMIN_STAFF, PATIENT, etc.
  label VARCHAR(100),
  description TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE permissions (
  id SERIAL PRIMARY KEY,
  code VARCHAR(120) UNIQUE NOT NULL,
  -- VIEW_PATIENT_CLINICAL_RECORDS, GENERATE_INVOICES, etc.
  description TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Relación many-to-many Rol <-> Permiso
CREATE TABLE role_permissions (
  role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
  permission_id INTEGER NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (role_id, permission_id)
);

-- =============================
-- 2) Usuarios / Identidad
-- =============================
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  username VARCHAR(100) UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  role_id INTEGER NOT NULL REFERENCES roles(id),
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  two_fa_enabled BOOLEAN NOT NULL DEFAULT FALSE,
  two_fa_secret VARCHAR(255),
  two_fa_expires_at TIMESTAMPTZ,
  two_fa_attempts INTEGER NOT NULL DEFAULT 0,
  password_reset_token VARCHAR(255),
  password_reset_expires TIMESTAMPTZ,
  last_login_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_users_role_id ON users(role_id);

-- =============================
-- 3) Catálogos: Áreas y Especialidades
-- =============================
CREATE TABLE areas (
  id SERIAL PRIMARY KEY,
  name VARCHAR(120) UNIQUE NOT NULL,
  description TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE specialties (
  id SERIAL PRIMARY KEY,
  name VARCHAR(120) UNIQUE NOT NULL,
  description TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =============================
-- 4) Empleados
-- =============================
CREATE TABLE employees (
  id SERIAL PRIMARY KEY,
  user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE
  SET
    NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    -- PSYCHOLOGIST, PSYCHIATRIST, TECHNICIAN, MAINTENANCE, ADMIN_STAFF
    license_number VARCHAR(100),
    -- aplica a profesionales
    area_id INTEGER REFERENCES areas(id) ON DELETE
  SET
    NULL,
    base_salary NUMERIC(12, 2) NOT NULL DEFAULT 0,
    session_rate NUMERIC(12, 2) NOT NULL DEFAULT 0,
    igss_percentage NUMERIC(5, 2) NOT NULL DEFAULT 0,
    hired_at DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    -- ACTIVE, INACTIVE
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_employee_status CHECK (status IN ('ACTIVE', 'INACTIVE'))
);

CREATE INDEX idx_employees_area_id ON employees(area_id);

CREATE TABLE employee_specialties (
  employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
  specialty_id INTEGER NOT NULL REFERENCES specialties(id) ON DELETE CASCADE,
  PRIMARY KEY (employee_id, specialty_id)
);

-- =============================
-- 5) Pacientes
-- =============================
CREATE TABLE patients (
  id SERIAL PRIMARY KEY,
  user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE
  SET
    NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    dob DATE,
    gender VARCHAR(20),
    marital_status VARCHAR(30),
    occupation VARCHAR(120),
    education_level VARCHAR(120),
    address TEXT,
    phone VARCHAR(50),
    email VARCHAR(255),
    emergency_contact_name VARCHAR(150),
    emergency_contact_relationship VARCHAR(80),
    emergency_contact_phone VARCHAR(50),
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    -- ACTIVE, INACTIVE
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_patient_status CHECK (status IN ('ACTIVE', 'INACTIVE'))
);

CREATE INDEX idx_patients_lastname ON patients(last_name);

-- =============================
-- 6) Historia Clínica (según plantilla)
-- =============================
CREATE TABLE clinical_records (
  id SERIAL PRIMARY KEY,
  patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
  record_number VARCHAR(50) UNIQUE,
  -- Número de Historia Clínica
  institution_name VARCHAR(150),
  service VARCHAR(120),
  -- Psicología clínica, neuropsicología, etc.
  opening_date DATE,
  responsible_employee_id INTEGER REFERENCES employees(id) ON DELETE
  SET
    NULL,
    responsible_license VARCHAR(100),
    referral_source VARCHAR(150),
    -- quién refiere
    chief_complaint TEXT,
    -- motivo de consulta
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    -- ACTIVE, CLOSED
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_clinical_record_status CHECK (status IN ('ACTIVE', 'CLOSED'))
);

CREATE INDEX idx_clinical_records_patient ON clinical_records(patient_id);

-- Antecedentes
CREATE TABLE clinical_backgrounds (
  id SERIAL PRIMARY KEY,
  clinical_record_id INTEGER NOT NULL UNIQUE REFERENCES clinical_records(id) ON DELETE CASCADE,
  family_structure TEXT,
  significant_family_relations TEXT,
  family_psych_history TEXT,
  family_events TEXT,
  developmental_history TEXT,
  academic_work_history TEXT,
  medical_history TEXT,
  current_medication TEXT,
  alcohol_use_level VARCHAR(30),
  tobacco_use_level VARCHAR(30),
  drug_use_details TEXT,
  previous_treatments TEXT,
  hospitalizations TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Evaluación inicial (Likert + observaciones)
CREATE TABLE initial_assessments (
  id SERIAL PRIMARY KEY,
  clinical_record_id INTEGER NOT NULL UNIQUE REFERENCES clinical_records(id) ON DELETE CASCADE,
  mood_level SMALLINT,
  anxiety_level SMALLINT,
  social_functioning SMALLINT,
  sleep_quality SMALLINT,
  appetite_level SMALLINT,
  general_observations TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_likert_mood CHECK (
    mood_level IS NULL
    OR mood_level BETWEEN 1
    AND 5
  ),
  CONSTRAINT chk_likert_anxiety CHECK (
    anxiety_level IS NULL
    OR anxiety_level BETWEEN 1
    AND 5
  ),
  CONSTRAINT chk_likert_social CHECK (
    social_functioning IS NULL
    OR social_functioning BETWEEN 1
    AND 5
  ),
  CONSTRAINT chk_likert_sleep CHECK (
    sleep_quality IS NULL
    OR sleep_quality BETWEEN 1
    AND 5
  ),
  CONSTRAINT chk_likert_appetite CHECK (
    appetite_level IS NULL
    OR appetite_level BETWEEN 1
    AND 5
  )
);

-- Pruebas psicológicas aplicadas
CREATE TABLE psychological_tests (
  id SERIAL PRIMARY KEY,
  clinical_record_id INTEGER NOT NULL REFERENCES clinical_records(id) ON DELETE CASCADE,
  test_name VARCHAR(150) NOT NULL,
  application_date DATE,
  result_value VARCHAR(100),
  interpretation TEXT,
  attachment_path TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_psych_tests_record ON psychological_tests(clinical_record_id);

-- Impresión diagnóstica
CREATE TABLE diagnostic_impressions (
  id SERIAL PRIMARY KEY,
  clinical_record_id INTEGER NOT NULL UNIQUE REFERENCES clinical_records(id) ON DELETE CASCADE,
  main_diagnosis_code VARCHAR(50),
  main_diagnosis_description TEXT,
  secondary_diagnosis_code VARCHAR(50),
  predisposing_factors TEXT,
  precipitating_factors TEXT,
  maintaining_factors TEXT,
  functioning_level SMALLINT,
  -- 0-100
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_functioning_level CHECK (
    functioning_level IS NULL
    OR functioning_level BETWEEN 0
    AND 100
  )
);

-- Plan de intervención
CREATE TABLE intervention_plans (
  id SERIAL PRIMARY KEY,
  clinical_record_id INTEGER NOT NULL UNIQUE REFERENCES clinical_records(id) ON DELETE CASCADE,
  short_term_goal TEXT,
  medium_term_goal TEXT,
  long_term_goal TEXT,
  modality VARCHAR(40),
  -- Individual, Familiar, Pareja, Grupo
  therapeutic_approach TEXT,
  -- texto (puedes normalizar luego si quieres)
  frequency VARCHAR(40),
  -- Semanal, Quincenal...
  sessions_per_week SMALLINT,
  estimated_duration_weeks SMALLINT,
  session_cost NUMERIC(12, 2),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Notas por sesión / progreso
CREATE TABLE sessions (
  id SERIAL PRIMARY KEY,
  clinical_record_id INTEGER NOT NULL REFERENCES clinical_records(id) ON DELETE CASCADE,
  professional_id INTEGER REFERENCES employees(id) ON DELETE
  SET
    NULL,
    session_datetime TIMESTAMPTZ NOT NULL,
    session_number INTEGER,
    attended BOOLEAN NOT NULL DEFAULT TRUE,
    absence_reason TEXT,
    topics TEXT,
    interventions TEXT,
    patient_response TEXT,
    assigned_tasks TEXT,
    observations TEXT,
    next_appointment_datetime TIMESTAMPTZ,
    digital_signature_path TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_sessions_record ON sessions(clinical_record_id);

CREATE INDEX idx_sessions_professional ON sessions(professional_id);

-- Evaluaciones periódicas
CREATE TABLE periodic_evaluations (
  id SERIAL PRIMARY KEY,
  clinical_record_id INTEGER NOT NULL REFERENCES clinical_records(id) ON DELETE CASCADE,
  evaluation_date DATE NOT NULL,
  evaluation_type VARCHAR(30),
  -- Parcial, Seguimiento, Final
  observed_progress TEXT,
  achieved_goals TEXT,
  pending_goals TEXT,
  recommendations TEXT,
  progress_scale SMALLINT,
  -- 1-10
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_progress_scale CHECK (
    progress_scale IS NULL
    OR progress_scale BETWEEN 1
    AND 10
  )
);

CREATE INDEX idx_periodic_eval_record ON periodic_evaluations(clinical_record_id);

-- Alta terapéutica
CREATE TABLE therapeutic_discharges (
  id SERIAL PRIMARY KEY,
  clinical_record_id INTEGER NOT NULL UNIQUE REFERENCES clinical_records(id) ON DELETE CASCADE,
  discharge_date DATE NOT NULL,
  discharge_reason VARCHAR(150),
  discharge_status TEXT,
  post_treatment_recommendations TEXT,
  follow_up_planned BOOLEAN NOT NULL DEFAULT FALSE,
  follow_up_date DATE,
  patient_signature_path TEXT,
  psychologist_signature_path TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Tareas asignadas al paciente
CREATE TABLE patient_tasks (
  id SERIAL PRIMARY KEY,
  patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
  clinical_record_id INTEGER REFERENCES clinical_records(id) ON DELETE
  SET
    NULL,
    assigned_by_employee_id INTEGER REFERENCES employees(id) ON DELETE
  SET
    NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    due_date DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    -- PENDING, COMPLETED, CANCELLED
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_task_status CHECK (status IN ('PENDING', 'COMPLETED', 'CANCELLED'))
);

CREATE INDEX idx_patient_tasks_patient ON patient_tasks(patient_id);

-- Advertencias / alertas
CREATE TABLE patient_alerts (
  id SERIAL PRIMARY KEY,
  patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
  created_by_employee_id INTEGER REFERENCES employees(id) ON DELETE
  SET
    NULL,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(10) NOT NULL DEFAULT 'LOW',
    -- LOW, MEDIUM, HIGH
    message TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at TIMESTAMPTZ,
    CONSTRAINT chk_alert_severity CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH'))
);

CREATE INDEX idx_patient_alerts_patient ON patient_alerts(patient_id);

-- Notas confidenciales
CREATE TABLE confidential_notes (
  id SERIAL PRIMARY KEY,
  patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
  clinical_record_id INTEGER NOT NULL REFERENCES clinical_records(id) ON DELETE CASCADE,
  author_employee_id INTEGER REFERENCES employees(id) ON DELETE
  SET
    NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_conf_notes_record ON confidential_notes(clinical_record_id);

-- Adjuntos clínicos
CREATE TABLE clinical_attachments (
  id SERIAL PRIMARY KEY,
  clinical_record_id INTEGER NOT NULL REFERENCES clinical_records(id) ON DELETE CASCADE,
  attachment_type VARCHAR(50) NOT NULL,
  -- CONSENT_FORM, TEST_RESULT, COMMUNICATION, etc.
  file_path TEXT NOT NULL,
  description TEXT,
  uploaded_by_employee_id INTEGER REFERENCES employees(id) ON DELETE
  SET
    NULL,
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_clinical_attach_record ON clinical_attachments(clinical_record_id);

-- =============================
-- 7) Citas
-- =============================
CREATE TABLE appointments (
  id SERIAL PRIMARY KEY,
  patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
  professional_id INTEGER REFERENCES employees(id) ON DELETE
  SET
    NULL,
    specialty_id INTEGER REFERENCES specialties(id) ON DELETE
  SET
    NULL,
    appointment_type VARCHAR(50),
    start_datetime TIMESTAMPTZ NOT NULL,
    end_datetime TIMESTAMPTZ NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'SCHEDULED',
    -- SCHEDULED, COMPLETED, CANCELLED, NO_SHOW
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_appt_status CHECK (
      status IN ('SCHEDULED', 'COMPLETED', 'CANCELLED', 'NO_SHOW')
    ),
    CONSTRAINT chk_appt_time CHECK (end_datetime > start_datetime)
);

CREATE INDEX idx_appointments_patient ON appointments(patient_id);

CREATE INDEX idx_appointments_professional ON appointments(professional_id);

CREATE INDEX idx_appointments_start ON appointments(start_datetime);

-- (opcional) vínculo de una sesión con una cita: lo manejas en app,
-- o si lo quieres estricto: agrega appointment_id en sessions.
ALTER TABLE
  sessions
ADD
  COLUMN appointment_id INTEGER REFERENCES appointments(id) ON DELETE
SET
  NULL;

CREATE INDEX idx_sessions_appointment ON sessions(appointment_id);

-- =============================
-- 8) Facturación / Pagos
-- =============================
CREATE TABLE payment_methods (
  id SERIAL PRIMARY KEY,
  name VARCHAR(80) UNIQUE NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE services (
  id SERIAL PRIMARY KEY,
  code VARCHAR(50) UNIQUE NOT NULL,
  name VARCHAR(150) NOT NULL,
  area_id INTEGER REFERENCES areas(id) ON DELETE
  SET
    NULL,
    default_price NUMERIC(12, 2) NOT NULL DEFAULT 0,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE invoices (
  id SERIAL PRIMARY KEY,
  invoice_number VARCHAR(60) UNIQUE NOT NULL,
  patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE RESTRICT,
  created_by_employee_id INTEGER REFERENCES employees(id) ON DELETE
  SET
    NULL,
    invoice_date DATE NOT NULL DEFAULT CURRENT_DATE,
    due_date DATE,
    currency VARCHAR(10) NOT NULL DEFAULT 'GTQ',
    total_amount NUMERIC(12, 2) NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'ISSUED',
    -- DRAFT, ISSUED, PAID, CANCELLED
    pdf_path TEXT,
    -- S3 path si guardas comprobante/factura
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_invoice_status CHECK (status IN ('DRAFT', 'ISSUED', 'PAID', 'CANCELLED'))
);

CREATE INDEX idx_invoices_patient ON invoices(patient_id);

CREATE INDEX idx_invoices_status ON invoices(status);

-- Inventario/Productos se define antes de invoice_items para FK opcionales
-- =============================
-- 9) Inventario
-- =============================
CREATE TABLE products (
  id SERIAL PRIMARY KEY,
  sku VARCHAR(80) UNIQUE,
  name VARCHAR(150) NOT NULL,
  description TEXT,
  product_type VARCHAR(30) NOT NULL DEFAULT 'OTHER',
  -- MEDICATION, TOOL, OTHER
  unit VARCHAR(30),
  cost_price NUMERIC(12, 2) NOT NULL DEFAULT 0,
  sale_price NUMERIC(12, 2) NOT NULL DEFAULT 0,
  min_stock INTEGER NOT NULL DEFAULT 0,
  current_stock INTEGER NOT NULL DEFAULT 0,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_product_type CHECK (product_type IN ('MEDICATION', 'TOOL', 'OTHER')),
  CONSTRAINT chk_stock_nonnegative CHECK (
    current_stock >= 0
    AND min_stock >= 0
  )
);

CREATE INDEX idx_products_type ON products(product_type);

-- Items de factura (servicios o productos)
CREATE TABLE invoice_items (
  id SERIAL PRIMARY KEY,
  invoice_id INTEGER NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
  service_id INTEGER REFERENCES services(id) ON DELETE
  SET
    NULL,
    product_id INTEGER REFERENCES products(id) ON DELETE
  SET
    NULL,
    description TEXT,
    quantity NUMERIC(12, 2) NOT NULL DEFAULT 1,
    unit_price NUMERIC(12, 2) NOT NULL DEFAULT 0,
    total_amount NUMERIC(12, 2) NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_item_qty CHECK (quantity > 0),
    CONSTRAINT chk_item_one_ref CHECK (
      (
        service_id IS NOT NULL
        AND product_id IS NULL
      )
      OR (
        service_id IS NULL
        AND product_id IS NOT NULL
      )
    )
);

CREATE INDEX idx_invoice_items_invoice ON invoice_items(invoice_id);

-- Pagos
CREATE TABLE payments (
  id SERIAL PRIMARY KEY,
  invoice_id INTEGER NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
  payment_method_id INTEGER REFERENCES payment_methods(id) ON DELETE
  SET
    NULL,
    amount NUMERIC(12, 2) NOT NULL,
    paid_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    reference VARCHAR(120),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_payment_amount CHECK (amount > 0)
);

CREATE INDEX idx_payments_invoice ON payments(invoice_id);

-- Movimientos de inventario
CREATE TABLE inventory_movements (
  id SERIAL PRIMARY KEY,
  product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
  movement_type VARCHAR(20) NOT NULL,
  -- IN, OUT, ADJUSTMENT
  quantity INTEGER NOT NULL,
  movement_date TIMESTAMPTZ NOT NULL DEFAULT now(),
  reason VARCHAR(50),
  -- PURCHASE, SALE, PRESCRIPTION_DELIVERY, ADJUSTMENT, etc.
  related_invoice_item_id INTEGER REFERENCES invoice_items(id) ON DELETE
  SET
    NULL,
    created_by_employee_id INTEGER REFERENCES employees(id) ON DELETE
  SET
    NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_movement_type CHECK (movement_type IN ('IN', 'OUT', 'ADJUSTMENT')),
    CONSTRAINT chk_movement_qty CHECK (quantity > 0)
);

CREATE INDEX idx_inventory_movements_product ON inventory_movements(product_id);

-- =============================
-- 10) Prescripciones / Entregas de medicación
-- =============================
CREATE TABLE prescriptions (
  id SERIAL PRIMARY KEY,
  patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
  clinical_record_id INTEGER REFERENCES clinical_records(id) ON DELETE
  SET
    NULL,
    prescribed_by_employee_id INTEGER REFERENCES employees(id) ON DELETE
  SET
    NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    notes TEXT
);

CREATE INDEX idx_prescriptions_patient ON prescriptions(patient_id);

CREATE TABLE prescription_items (
  id SERIAL PRIMARY KEY,
  prescription_id INTEGER NOT NULL REFERENCES prescriptions(id) ON DELETE CASCADE,
  product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
  dose VARCHAR(80),
  frequency VARCHAR(80),
  duration_days INTEGER,
  instructions TEXT
);

CREATE INDEX idx_prescription_items_presc ON prescription_items(prescription_id);

CREATE TABLE medication_deliveries (
  id SERIAL PRIMARY KEY,
  prescription_item_id INTEGER NOT NULL REFERENCES prescription_items(id) ON DELETE CASCADE,
  delivered_by_employee_id INTEGER REFERENCES employees(id) ON DELETE
  SET
    NULL,
    quantity INTEGER NOT NULL,
    delivered_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_delivery_qty CHECK (quantity > 0)
);

-- =============================
-- 11) Nómina
-- =============================
CREATE TABLE payroll_periods (
  id SERIAL PRIMARY KEY,
  period_start DATE NOT NULL,
  period_end DATE NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'OPEN',
  -- OPEN, CLOSED, PAID
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_payroll_period CHECK (period_end >= period_start),
  CONSTRAINT chk_payroll_status CHECK (status IN ('OPEN', 'CLOSED', 'PAID'))
);

CREATE TABLE payroll_records (
  id SERIAL PRIMARY KEY,
  employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE RESTRICT,
  period_id INTEGER NOT NULL REFERENCES payroll_periods(id) ON DELETE RESTRICT,
  base_salary_amount NUMERIC(12, 2) NOT NULL DEFAULT 0,
  sessions_count INTEGER NOT NULL DEFAULT 0,
  sessions_amount NUMERIC(12, 2) NOT NULL DEFAULT 0,
  bonuses_amount NUMERIC(12, 2) NOT NULL DEFAULT 0,
  igss_deduction NUMERIC(12, 2) NOT NULL DEFAULT 0,
  other_deductions NUMERIC(12, 2) NOT NULL DEFAULT 0,
  total_pay NUMERIC(12, 2) NOT NULL DEFAULT 0,
  paid_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_payroll_employee_period UNIQUE (employee_id, period_id)
);

CREATE INDEX idx_payroll_records_employee ON payroll_records(employee_id);

-- =============================
-- 12) Auditoría
-- =============================
CREATE TABLE audit_logs (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id) ON DELETE
  SET
    NULL,
    action VARCHAR(20) NOT NULL,
    -- VIEW, CREATE, UPDATE, DELETE, LOGIN, etc.
    entity VARCHAR(50) NOT NULL,
    -- PATIENT, CLINICAL_RECORD, INVOICE, etc.
    entity_id VARCHAR(60),
    -- id como string por flexibilidad
    timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    ip_address VARCHAR(64),
    details JSONB,
    CONSTRAINT chk_audit_action CHECK (
      action IN (
        'VIEW',
        'CREATE',
        'UPDATE',
        'DELETE',
        'LOGIN',
        'LOGOUT',
        'EXPORT'
      )
    )
);

CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);

CREATE INDEX idx_audit_logs_entity ON audit_logs(entity, entity_id);

-- =============================
-- Agenda por especialidad (mínimo)
-- Disponibilidad semanal del profesional
-- =============================

CREATE TABLE employee_availability (
  id            SERIAL PRIMARY KEY,
  employee_id   INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,

  -- 0=Domingo ... 6=Sábado (o ajusta a tu convención)
  day_of_week   SMALLINT NOT NULL,
  start_time    TIME NOT NULL,
  end_time      TIME NOT NULL,

  -- Para "agenda por especialidad"
  specialty_id  INTEGER REFERENCES specialties(id) ON DELETE SET NULL,

  is_active     BOOLEAN NOT NULL DEFAULT TRUE,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT chk_day_of_week CHECK (day_of_week BETWEEN 0 AND 6),
  CONSTRAINT chk_availability_time CHECK (end_time > start_time)
);

CREATE INDEX idx_employee_availability_employee ON employee_availability(employee_id);
CREATE INDEX idx_employee_availability_specialty ON employee_availability(specialty_id);
CREATE INDEX idx_employee_availability_day ON employee_availability(day_of_week);



COMMIT;