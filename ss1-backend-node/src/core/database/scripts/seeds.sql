BEGIN;

-- =============================
-- ROLES
-- =============================
INSERT INTO
  roles (name, label, description)
VALUES
  (
    'SUPER_ADMIN',
    'Super Administrador',
    'Acceso total y administración de roles/permisos'
  ),
  (
    'ADMIN_STAFF',
    'Administrativo',
    'Personal administrativo (secretaría, caja, etc.)'
  ),
  (
    'PSYCHOLOGIST',
    'Psicólogo',
    'Profesional que gestiona historial clínico y sesiones'
  ),
  (
    'PSYCHIATRIST',
    'Psiquiatra',
    'Profesional que gestiona historial clínico y medicación'
  ),
  (
    'TECHNICIAN',
    'Técnico',
    'Soporte técnico / pruebas / asistencia'
  ),
  (
    'MAINTENANCE',
    'Mantenimiento',
    'Personal de mantenimiento (acceso limitado)'
  ),
  (
    'PATIENT',
    'Paciente',
    'Portal del paciente (ver info propia)'
  ) ON CONFLICT (name) DO NOTHING;

-- =============================
-- PERMISSIONS (base)
-- =============================
INSERT INTO
  permissions (code, description)
VALUES
  -- Administración RBAC (solo SUPER_ADMIN debería poder)
  ('MANAGE_ROLES', 'Crear/editar roles'),
  ('MANAGE_PERMISSIONS', 'Crear/editar permisos'),
  (
    'ASSIGN_ROLE_PERMISSIONS',
    'Asignar/quitar permisos a roles'
  ),
  -- Gestión de Usuarios
  ('VIEW_USERS', 'Ver listado de usuarios'),
  ('CREATE_USERS', 'Crear usuarios'),
  ('EDIT_USERS', 'Editar usuarios'),
  -- Gestión de Empleados
  ('CREATE_EMPLOYEES', 'Crear empleados'),
  ('EDIT_EMPLOYEES', 'Editar empleados'),
  ('VIEW_EMPLOYEES', 'Ver listado de empleados'),
  -- Áreas y Especialidades
  ('MANAGE_AREAS', 'Gestionar áreas'),
  (
    'MANAGE_SPECIALTIES',
    'Gestionar especialidades'
  ),
  -- Pacientes / Historia clínica
  (
    'VIEW_PATIENTS',
    'Ver listado/detalle de pacientes'
  ),
  ('CREATE_PATIENTS', 'Crear pacientes'),
  ('EDIT_PATIENTS', 'Editar pacientes'),
  (
    'VIEW_PATIENT_CLINICAL_RECORDS',
    'Ver historiales clínicos de pacientes'
  ),
  (
    'CREATE_PATIENT_CLINICAL_RECORDS',
    'Crear historiales clínicos'
  ),
  (
    'EDIT_PATIENT_CLINICAL_RECORDS',
    'Editar historiales clínicos'
  ),
  (
    'VIEW_CONFIDENTIAL_NOTES',
    'Ver notas confidenciales'
  ),
  (
    'CREATE_CONFIDENTIAL_NOTES',
    'Crear notas confidenciales'
  ),
  ('VIEW_SESSIONS', 'Ver sesiones'),
  (
    'CREATE_SESSIONS',
    'Crear sesiones/notas de progreso'
  ),
  (
    'EDIT_SESSIONS',
    'Editar sesiones/notas de progreso'
  ),
  (
    'ASSIGN_PATIENT_TASKS',
    'Asignar tareas/actividades a paciente'
  ),
  (
    'MANAGE_PATIENT_ALERTS',
    'Crear/gestionar advertencias/alertas'
  ),
  -- Citas
  (
    'VIEW_SCHEDULED_APPOINTMENTS',
    'Ver citas/agendas'
  ),
  ('CREATE_APPOINTMENTS', 'Crear citas'),
  ('EDIT_APPOINTMENTS', 'Editar/reprogramar citas'),
  ('COMPLETE_APPOINTMENTS', 'Completar citas'),
  ('CANCEL_APPOINTMENTS', 'Cancelar citas'),
  -- Inventario
  ('VIEW_INVENTORY', 'Ver inventario'),
  (
    'MANAGE_INVENTORY',
    'Crear/editar productos y movimientos de inventario'
  ),
  -- Prescripciones / entregas (ligado a inventario)
  ('CREATE_PRESCRIPTIONS', 'Crear prescripciones'),
  (
    'DELIVER_MEDICATION',
    'Registrar entregas de medicación'
  ),
  -- Facturación y pagos
  ('VIEW_INVOICES', 'Ver facturas'),
  ('GENERATE_INVOICES', 'Generar/emitir facturas'),
  ('REGISTER_PAYMENTS', 'Registrar pagos'),
  (
    'VIEW_ACCOUNTS_RECEIVABLE',
    'Ver cuentas por cobrar'
  ),
  -- Nómina
  ('VIEW_PAYROLL', 'Ver nómina'),
  (
    'MANAGE_PAYROLL',
    'Procesar nómina (bonos, descuentos, pagos)'
  ),
  -- Reportes
  (
    'VIEW_REPORTS_FINANCIAL',
    'Ver reportes financieros'
  ),
  ('VIEW_REPORTS_CLINICAL', 'Ver reportes clínicos'),
  (
    'VIEW_REPORTS_INVENTORY',
    'Ver reportes de inventario'
  ),
  ('VIEW_REPORTS_HR', 'Ver reportes de RRHH'),
  -- Auditoría (si quieres restringir quién ve logs)
  ('VIEW_AUDIT_LOGS', 'Ver logs de auditoría') ON CONFLICT (code) DO NOTHING;

-- =============================
-- ROLE_PERMISSIONS
-- (Recuerda: SUPER_ADMIN bypass en código,
--  pero igual puedes asignarle permisos RBAC para endpoints admin si quieres)
-- =============================
-- Helper CTE: tomar ids
WITH r AS (
  SELECT
    id,
    name
  FROM
    roles
),
p AS (
  SELECT
    id,
    code
  FROM
    permissions
) -- SUPER_ADMIN (opcional asignar, aunque en guard haces bypass)
INSERT INTO
  role_permissions (role_id, permission_id)
SELECT
  r.id,
  p.id
FROM
  r,
  p
WHERE
  r.name = 'SUPER_ADMIN'
  AND p.code IN (
    'MANAGE_ROLES',
    'MANAGE_PERMISSIONS',
    'ASSIGN_ROLE_PERMISSIONS',
    'VIEW_AUDIT_LOGS'
  ) ON CONFLICT DO NOTHING;

-- PSYCHOLOGIST
WITH r AS (
  SELECT
    id
  FROM
    roles
  WHERE
    name = 'PSYCHOLOGIST'
),
p AS (
  SELECT
    id,
    code
  FROM
    permissions
)
INSERT INTO
  role_permissions (role_id, permission_id)
SELECT
  (
    SELECT
      id
    FROM
      r
  ),
  p.id
FROM
  p
WHERE
  p.code IN (
    'VIEW_PATIENTS',
    'VIEW_PATIENT_CLINICAL_RECORDS',
    'CREATE_PATIENT_CLINICAL_RECORDS',
    'EDIT_PATIENT_CLINICAL_RECORDS',
    'VIEW_SESSIONS',
    'CREATE_SESSIONS',
    'EDIT_SESSIONS',
    'COMPLETE_APPOINTMENTS',
    'ASSIGN_PATIENT_TASKS',
    'MANAGE_PATIENT_ALERTS',
    'VIEW_SCHEDULED_APPOINTMENTS',
    'CREATE_APPOINTMENTS',
    'CANCEL_APPOINTMENTS',
    'VIEW_CONFIDENTIAL_NOTES',
    'CREATE_CONFIDENTIAL_NOTES'
  ) ON CONFLICT DO NOTHING;

-- PSYCHIATRIST (incluye prescripción/entregas)
WITH r AS (
  SELECT
    id
  FROM
    roles
  WHERE
    name = 'PSYCHIATRIST'
),
p AS (
  SELECT
    id,
    code
  FROM
    permissions
)
INSERT INTO
  role_permissions (role_id, permission_id)
SELECT
  (
    SELECT
      id
    FROM
      r
  ),
  p.id
FROM
  p
WHERE
  p.code IN (
    'VIEW_PATIENTS',
    'VIEW_PATIENT_CLINICAL_RECORDS',
    'CREATE_PATIENT_CLINICAL_RECORDS',
    'EDIT_PATIENT_CLINICAL_RECORDS',
    'VIEW_SESSIONS',
    'CREATE_SESSIONS',
    'EDIT_SESSIONS',
    'CREATE_PRESCRIPTIONS',
    'COMPLETE_APPOINTMENTS',
    'DELIVER_MEDICATION',
    'VIEW_INVENTORY',
    'VIEW_SCHEDULED_APPOINTMENTS',
    'CREATE_APPOINTMENTS',
    'CANCEL_APPOINTMENTS',
    'VIEW_CONFIDENTIAL_NOTES',
    'CREATE_CONFIDENTIAL_NOTES'
  ) ON CONFLICT DO NOTHING;

-- ADMIN_STAFF (secretaría/caja: ver + facturación + inventario según política)
-- Si quieres que sea "solo ver" info clínica, NO agregues EDIT_* aquí.
WITH r AS (
  SELECT
    id
  FROM
    roles
  WHERE
    name = 'ADMIN_STAFF'
),
p AS (
  SELECT
    id,
    code
  FROM
    permissions
)
INSERT INTO
  role_permissions (role_id, permission_id)
SELECT
  (
    SELECT
      id
    FROM
      r
  ),
  p.id
FROM
  p
WHERE
  p.code IN (
    'VIEW_PATIENTS',
    'CREATE_PATIENTS',
    'EDIT_PATIENTS',
    'VIEW_SCHEDULED_APPOINTMENTS',
    'CREATE_APPOINTMENTS',
    'EDIT_APPOINTMENTS',
    'CANCEL_APPOINTMENTS',
    'VIEW_INVOICES',
    'GENERATE_INVOICES',
    'REGISTER_PAYMENTS',
    'VIEW_ACCOUNTS_RECEIVABLE',
    'VIEW_INVENTORY',
    'MANAGE_INVENTORY',
    'VIEW_REPORTS_FINANCIAL',
    'VIEW_REPORTS_INVENTORY'
  ) ON CONFLICT DO NOTHING;

-- TECHNICIAN (muy limitado; ajusta según tu criterio)
WITH r AS (
  SELECT
    id
  FROM
    roles
  WHERE
    name = 'TECHNICIAN'
),
p AS (
  SELECT
    id,
    code
  FROM
    permissions
)
INSERT INTO
  role_permissions (role_id, permission_id)
SELECT
  (
    SELECT
      id
    FROM
      r
  ),
  p.id
FROM
  p
WHERE
  p.code IN (
    'VIEW_SCHEDULED_APPOINTMENTS',
    'VIEW_INVENTORY'
  ) ON CONFLICT DO NOTHING;

-- MAINTENANCE (limitado)
WITH r AS (
  SELECT
    id
  FROM
    roles
  WHERE
    name = 'MAINTENANCE'
),
p AS (
  SELECT
    id,
    code
  FROM
    permissions
)
INSERT INTO
  role_permissions (role_id, permission_id)
SELECT
  (
    SELECT
      id
    FROM
      r
  ),
  p.id
FROM
  p
WHERE
  p.code IN ('VIEW_SCHEDULED_APPOINTMENTS') ON CONFLICT DO NOTHING;

-- PATIENT (portal: solo acceso a lo propio; el “ownership” lo controla la app)
WITH r AS (
  SELECT
    id
  FROM
    roles
  WHERE
    name = 'PATIENT'
),
p AS (
  SELECT
    id,
    code
  FROM
    permissions
)
INSERT INTO
  role_permissions (role_id, permission_id)
SELECT
  (
    SELECT
      id
    FROM
      r
  ),
  p.id
FROM
  p
WHERE
  p.code IN ('VIEW_SCHEDULED_APPOINTMENTS') ON CONFLICT DO NOTHING;

-- =============================
-- SUPERADMIN USER (password_hash placeholder)
-- 1) Genera bcrypt hash en Node y reemplaza 'REPLACE_WITH_BCRYPT_HASH'
-- =============================
INSERT INTO
  users (
    email,
    username,
    password_hash,
    role_id,
    is_active,
    two_fa_enabled
  )
VALUES
  (
    'robertobau9091@gmail.com',
    'superadmin',
    '$2a$12$MOQvgXcUJyOqXgcuw/QG9.3qorXKb7ge.Bv0PnE3kGRofCTV9QRQK',
    (
      SELECT
        id
      FROM
        roles
      WHERE
        name = 'SUPER_ADMIN'
    ),
    TRUE,
    FALSE
  ) ON CONFLICT (email) DO NOTHING;

-- =============================
-- SUPERADMIN EMPLOYEE
-- =============================
INSERT INTO
  employees (
    user_id,
    first_name,
    last_name,
    base_salary,
    session_rate,
    igss_percentage,
    hired_at,
    status
  )
VALUES
  (
    (
      SELECT
        id
      FROM
        users
      WHERE
        email = 'robertobau9091@gmail.com'
    ),
    'Super',
    'Administrador',
    0.00,
    0.00,
    0.00,
    CURRENT_DATE,
    'ACTIVE'
  ) ON CONFLICT (user_id) DO NOTHING;

INSERT INTO
  areas (name, description)
VALUES
  (
    'Salud Mental Adultos',
    'Atención psicológica y psiquiátrica para pacientes adultos.'
  ),
  (
    'Salud Mental Infantil y Adolescente',
    'Evaluación y tratamiento psicológico para niños y adolescentes.'
  ),
  (
    'Psiquiatría',
    'Diagnóstico y tratamiento médico de trastornos mentales.'
  ),
  (
    'Psicología Clínica',
    'Evaluaciones psicológicas, terapia individual y grupal.'
  ),
  (
    'Neuropsicología',
    'Evaluación de funciones cognitivas y daño cerebral.'
  ),
  (
    'Trabajo Social',
    'Apoyo psicosocial, estudios socioeconómicos y acompañamiento familiar.'
  ),
  (
    'Administración',
    'Gestión administrativa, recepción y coordinación de citas.'
  ),
  (
    'Soporte Técnico',
    'Mantenimiento de sistemas, infraestructura tecnológica y soporte.'
  ),
  (
    'Mantenimiento General',
    'Mantenimiento de instalaciones físicas y servicios generales.'
  ) ON CONFLICT (name) DO NOTHING;

-- =========================================================
-- ESPECIALIDADES CLÍNICAS
-- =========================================================
INSERT INTO
  specialties (name, description)
VALUES
  (
    'Psicología Clínica',
    'Tratamiento terapéutico de trastornos emocionales y psicológicos.'
  ),
  (
    'Psicoterapia Cognitivo-Conductual',
    'Intervenciones basadas en la modificación de pensamientos y conductas.'
  ),
  (
    'Psiquiatría General',
    'Diagnóstico médico y tratamiento farmacológico de trastornos mentales.'
  ),
  (
    'Psiquiatría Infantil',
    'Atención psiquiátrica especializada en niños y adolescentes.'
  ),
  (
    'Terapia de Pareja',
    'Intervenciones terapéuticas para conflictos de pareja.'
  ),
  (
    'Terapia Familiar',
    'Tratamiento psicológico enfocado en dinámicas familiares.'
  ),
  (
    'Evaluación Psicológica',
    'Aplicación de pruebas psicológicas y elaboración de informes clínicos.'
  ),
  (
    'Neuropsicología Clínica',
    'Evaluación y rehabilitación de funciones cognitivas.'
  ),
  (
    'Manejo de Ansiedad y Estrés',
    'Tratamiento especializado para ansiedad, estrés y burnout.'
  ),
  (
    'Trastornos del Estado de Ánimo',
    'Atención a depresión, trastorno bipolar y alteraciones emocionales.'
  ),
  (
    'Adicciones',
    'Tratamiento psicológico y psiquiátrico de dependencias.'
  ),
  (
    'Orientación Vocacional',
    'Evaluación y acompañamiento para elección profesional.'
  ) ON CONFLICT (name) DO NOTHING;

COMMIT;

-- =========================================================
-- EXTRA SEEDS: +20 usuarios para probar paginación
-- (12 pacientes, 8 empleados) - mismo password_hash del superadmin
-- Pegar DESPUÉS del COMMIT; existente
-- =========================================================
BEGIN;

-- 12 pacientes
WITH new_users AS (
  INSERT INTO
    users (
      email,
      username,
      password_hash,
      role_id,
      is_active
    )
  SELECT
    'patient' || gs :: text || '@example.com' AS email,
    'patient' || gs :: text AS username,
    '$2a$12$MOQvgXcUJyOqXgcuw/QG9.3qorXKb7ge.Bv0PnE3kGRofCTV9QRQK' AS password_hash,
    (
      SELECT
        id
      FROM
        roles
      WHERE
        name = 'PATIENT'
    ) AS role_id,
    TRUE AS is_active
  FROM
    generate_series(1, 12) gs ON CONFLICT DO NOTHING RETURNING id,
    email
)
INSERT INTO
  patients (
    user_id,
    first_name,
    last_name,
    dob,
    gender,
    marital_status,
    occupation,
    education_level,
    address,
    phone,
    email,
    emergency_contact_name,
    emergency_contact_relationship,
    emergency_contact_phone,
    status
  )
SELECT
  u.id AS user_id,
  'Patient' || gs :: text AS first_name,
  'Test' || gs :: text AS last_name,
  DATE '1998-01-01' + (gs * 90) AS dob,
  CASE
    WHEN gs % 2 = 0 THEN 'F'
    ELSE 'M'
  END AS gender,
  CASE
    WHEN gs % 3 = 0 THEN 'MARRIED'
    ELSE 'SINGLE'
  END AS marital_status,
  'Occupation ' || gs :: text AS occupation,
  'High School' AS education_level,
  'Zona ' || (gs % 12 + 1) :: text || ', Quetzaltenango' AS address,
  '+502 5555-' || LPAD((3000 + gs) :: text, 4, '0') AS phone,
  u.email AS email,
  'Contacto ' || gs :: text AS emergency_contact_name,
  'FAMILY' AS emergency_contact_relationship,
  '+502 4444-' || LPAD((4000 + gs) :: text, 4, '0') AS emergency_contact_phone,
  'ACTIVE' AS status
FROM
  new_users u
  JOIN generate_series(1, 12) gs ON u.email = ('patient' || gs :: text || '@example.com') ON CONFLICT (user_id) DO NOTHING;

-- =========================================================
-- 8 empleados (roles coherentes, sin employee_type)
-- =========================================================
WITH emp_seed AS (
  SELECT
    gs,
    CASE (gs % 5)
      WHEN 0 THEN 'PSYCHOLOGIST'
      WHEN 1 THEN 'PSYCHIATRIST'
      WHEN 2 THEN 'TECHNICIAN'
      WHEN 3 THEN 'MAINTENANCE'
      ELSE 'ADMIN_STAFF'
    END AS role_name
  FROM generate_series(1, 8) gs
),
new_users AS (
  INSERT INTO users (
    email,
    username,
    password_hash,
    role_id,
    is_active
  )
  SELECT
    'employee' || e.gs::text || '@example.com' AS email,
    'employee' || e.gs::text AS username,
    '$2a$12$MOQvgXcUJyOqXgcuw/QG9.3qorXKb7ge.Bv0PnE3kGRofCTV9QRQK' AS password_hash,
    (
      SELECT id
      FROM roles
      WHERE name = e.role_name
    ) AS role_id,
    TRUE AS is_active
  FROM emp_seed e
  ON CONFLICT DO NOTHING
  RETURNING id, email
)
INSERT INTO employees (
  user_id,
  first_name,
  last_name,
  license_number,
  area_id,
  base_salary,
  session_rate,
  igss_percentage,
  hired_at,
  status
)
SELECT
  u.id AS user_id,
  'Employee' || e.gs::text AS first_name,
  'Test' || e.gs::text AS last_name,

  -- Licencia solo para perfiles clínicos (simulado por índice)
  CASE
    WHEN e.gs % 3 = 0 THEN 'LIC-' || LPAD(e.gs::text, 5, '0')
    ELSE NULL
  END AS license_number,

  NULL AS area_id,
  (3500 + e.gs * 200)::numeric(12,2) AS base_salary,

  -- Session rate solo si tiene licencia
  CASE
    WHEN e.gs % 3 = 0 THEN (250 + e.gs * 15)::numeric(12,2)
    ELSE 0::numeric(12,2)
  END AS session_rate,

  4.83::numeric(5,2) AS igss_percentage,
  DATE '2023-01-01' + (e.gs * 20) AS hired_at,
  'ACTIVE' AS status
FROM new_users u
JOIN emp_seed e
  ON u.email = ('employee' || e.gs::text || '@example.com')
ON CONFLICT (user_id) DO NOTHING;


COMMIT;