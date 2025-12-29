import { Model, RelationMappings, RelationMappingsThunk } from 'objection';
import { PatientModel } from 'src/modules/patients/entities/patient.entity';
import { ClinicalRecordModel } from 'src/modules/clinical-records/entities/clinical-record.entity';
import { EmployeeModel } from 'src/modules/employees/entities/employee.entity';

export class PatientTaskModel extends Model {
  static tableName = 'patient_tasks';

  id: number;
  patient_id: number;
  clinical_record_id: number | null;
  assigned_by_employee_id: number | null;
  title: string;
  description: string | null;
  due_date: Date | null;
  status: string;
  created_at: Date;
  updated_at: Date;

  // Relaciones
  patient?: PatientModel;
  clinical_record?: ClinicalRecordModel;
  assigned_by?: EmployeeModel;

  static get relationMappings(): RelationMappings | RelationMappingsThunk {
    return {
      patient: {
        relation: Model.BelongsToOneRelation,
        modelClass: PatientModel,
        join: {
          from: 'patient_tasks.patient_id',
          to: 'patients.id',
        },
      },
      clinical_record: {
        relation: Model.BelongsToOneRelation,
        modelClass: ClinicalRecordModel,
        join: {
          from: 'patient_tasks.clinical_record_id',
          to: 'clinical_records.id',
        },
      },
      assigned_by: {
        relation: Model.BelongsToOneRelation,
        modelClass: EmployeeModel,
        join: {
          from: 'patient_tasks.assigned_by_employee_id',
          to: 'employees.id',
        },
      },
    };
  }
}
