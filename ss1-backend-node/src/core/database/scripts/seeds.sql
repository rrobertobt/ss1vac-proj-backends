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
    'ASSIGN_PATIENT_TASKS',
    'MANAGE_PATIENT_ALERTS',
    'VIEW_SCHEDULED_APPOINTMENTS',
    'CREATE_APPOINTMENTS',
    'EDIT_APPOINTMENTS',
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
    'DELIVER_MEDICATION',
    'VIEW_INVENTORY',
    'VIEW_SCHEDULED_APPOINTMENTS',
    'CREATE_APPOINTMENTS',
    'EDIT_APPOINTMENTS',
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
    is_active
  )
VALUES
  (
    'superadmin@psifirm.local',
    'superadmin',
    'REPLACE_WITH_BCRYPT_HASH',
    (
      SELECT
        id
      FROM
        roles
      WHERE
        name = 'SUPER_ADMIN'
    ),
    TRUE
  ) ON CONFLICT (email) DO NOTHING;

COMMIT;