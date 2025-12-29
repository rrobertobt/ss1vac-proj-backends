import { Model, RelationMappings, RelationMappingsThunk } from 'objection';
import { PatientModel } from 'src/modules/patients/entities/patient.entity';
import { ClinicalRecordModel } from 'src/modules/clinical-records/entities/clinical-record.entity';
import { EmployeeModel } from 'src/modules/employees/entities/employee.entity';

export class ConfidentialNoteModel extends Model {
  static tableName = 'confidential_notes';

  id: number;
  patient_id: number;
  clinical_record_id: number;
  author_employee_id: number | null;
  content: string;
  created_at: Date;

  // Relaciones
  patient?: PatientModel;
  clinical_record?: ClinicalRecordModel;
  author?: EmployeeModel;

  static get relationMappings(): RelationMappings | RelationMappingsThunk {
    return {
      patient: {
        relation: Model.BelongsToOneRelation,
        modelClass: PatientModel,
        join: {
          from: 'confidential_notes.patient_id',
          to: 'patients.id',
        },
      },
      clinical_record: {
        relation: Model.BelongsToOneRelation,
        modelClass: ClinicalRecordModel,
        join: {
          from: 'confidential_notes.clinical_record_id',
          to: 'clinical_records.id',
        },
      },
      author: {
        relation: Model.BelongsToOneRelation,
        modelClass: EmployeeModel,
        join: {
          from: 'confidential_notes.author_employee_id',
          to: 'employees.id',
        },
      },
    };
  }
}
