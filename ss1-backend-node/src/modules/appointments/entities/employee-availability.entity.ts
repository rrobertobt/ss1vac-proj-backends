import { Model, RelationMappings, RelationMappingsThunk } from 'objection';
import { EmployeeModel } from 'src/modules/employees/entities/employee.entity';
import { SpecialtyModel } from 'src/modules/specialties/entities/specialty.entity';

export class EmployeeAvailabilityModel extends Model {
  static tableName = 'employee_availability';

  id: number;
  employee_id: number;
  day_of_week: number; // 0=Domingo, 6=Sábado
  start_time: string; // HH:MM:SS format
  end_time: string;
  specialty_id: number | null;
  is_active: boolean;
  created_at: Date;
  updated_at: Date;

  // Relaciones
  employee?: EmployeeModel;
  specialty?: SpecialtyModel;

  static get relationMappings(): RelationMappings | RelationMappingsThunk {
    return {
      employee: {
        relation: Model.BelongsToOneRelation,
        modelClass: EmployeeModel,
        join: {
          from: 'employee_availability.employee_id',
          to: 'employees.id',
        },
      },
      specialty: {
        relation: Model.BelongsToOneRelation,
        modelClass: SpecialtyModel,
        join: {
          from: 'employee_availability.specialty_id',
          to: 'specialties.id',
        },
      },
    };
  }
}
