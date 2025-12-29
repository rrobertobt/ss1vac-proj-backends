import { Model, RelationMappings, RelationMappingsThunk } from 'objection';
import { PatientModel } from 'src/modules/patients/entities/patient.entity';
import { EmployeeModel } from 'src/modules/employees/entities/employee.entity';
import { SpecialtyModel } from 'src/modules/specialties/entities/specialty.entity';

export class AppointmentModel extends Model {
  static tableName = 'appointments';

  id: number;
  patient_id: number;
  professional_id: number | null;
  specialty_id: number | null;
  appointment_type: string | null;
  start_datetime: Date;
  end_datetime: Date;
  status: string;
  notes: string | null;
  created_at: Date;
  updated_at: Date;

  // Relaciones
  patient?: PatientModel;
  professional?: EmployeeModel;
  specialty?: SpecialtyModel;

  static get relationMappings(): RelationMappings | RelationMappingsThunk {
    return {
      patient: {
        relation: Model.BelongsToOneRelation,
        modelClass: PatientModel,
        join: {
          from: 'appointments.patient_id',
          to: 'patients.id',
        },
      },
      professional: {
        relation: Model.BelongsToOneRelation,
        modelClass: EmployeeModel,
        join: {
          from: 'appointments.professional_id',
          to: 'employees.id',
        },
      },
      specialty: {
        relation: Model.BelongsToOneRelation,
        modelClass: SpecialtyModel,
        join: {
          from: 'appointments.specialty_id',
          to: 'specialties.id',
        },
      },
    };
  }
}
