import { Model, RelationMappings, RelationMappingsThunk } from 'objection';
import { PatientModel } from 'src/modules/patients/entities/patient.entity';
import { EmployeeModel } from 'src/modules/employees/entities/employee.entity';

export class ClinicalRecordModel extends Model {
  static tableName = 'clinical_records';

  id: number;
  patient_id: number;
  record_number: string | null;
  institution_name: string | null;
  service: string | null;
  opening_date: Date | null;
  responsible_employee_id: number | null;
  responsible_license: string | null;
  referral_source: string | null;
  chief_complaint: string | null;
  status: string;
  created_at: Date;
  updated_at: Date;

  // Relaciones
  patient?: PatientModel;
  responsible_employee?: EmployeeModel;

  static get relationMappings(): RelationMappings | RelationMappingsThunk {
    return {
      patient: {
        relation: Model.BelongsToOneRelation,
        modelClass: PatientModel,
        join: {
          from: 'clinical_records.patient_id',
          to: 'patients.id',
        },
      },
      responsible_employee: {
        relation: Model.BelongsToOneRelation,
        modelClass: EmployeeModel,
        join: {
          from: 'clinical_records.responsible_employee_id',
          to: 'employees.id',
        },
      },
    };
  }
}
