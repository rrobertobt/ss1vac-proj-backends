import { Model, RelationMappings, RelationMappingsThunk } from 'objection';
import { ClinicalRecordModel } from 'src/modules/clinical-records/entities/clinical-record.entity';
import { EmployeeModel } from 'src/modules/employees/entities/employee.entity';

export class SessionModel extends Model {
  static tableName = 'sessions';

  id: number;
  clinical_record_id: number;
  professional_id: number | null;
  session_datetime: Date;
  session_number: number | null;
  attended: boolean;
  absence_reason: string | null;
  topics: string | null;
  interventions: string | null;
  patient_response: string | null;
  assigned_tasks: string | null;
  observations: string | null;
  next_appointment_datetime: Date | null;
  digital_signature_path: string | null;
  appointment_id: number | null;
  created_at: Date;
  updated_at: Date;

  // Relaciones
  clinical_record?: ClinicalRecordModel;
  professional?: EmployeeModel;

  static get relationMappings(): RelationMappings | RelationMappingsThunk {
    return {
      clinical_record: {
        relation: Model.BelongsToOneRelation,
        modelClass: ClinicalRecordModel,
        join: {
          from: 'sessions.clinical_record_id',
          to: 'clinical_records.id',
        },
      },
      professional: {
        relation: Model.BelongsToOneRelation,
        modelClass: EmployeeModel,
        join: {
          from: 'sessions.professional_id',
          to: 'employees.id',
        },
      },
    };
  }
}
