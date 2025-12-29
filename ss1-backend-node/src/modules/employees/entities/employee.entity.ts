import { Model, RelationMappings, RelationMappingsThunk } from 'objection';
import { UserModel } from 'src/modules/users/entities/user.entity';
import { AreaModel } from 'src/modules/areas/entities/area.entity';
import { SpecialtyModel } from 'src/modules/specialties/entities/specialty.entity';
import { EmployeeAvailabilityModel } from './employee-availability.entity';

export class EmployeeModel extends Model {
  static tableName = 'employees';

  id: number;
  user_id: number | null;
  first_name: string;
  last_name: string;
  license_number: string | null;
  area_id: number | null;
  base_salary: number;
  session_rate: number;
  igss_percentage: number;
  hired_at: Date | null;
  status: string;
  created_at: Date;
  updated_at: Date;

  // Relaciones
  user?: UserModel;
  area?: AreaModel;
  specialties?: SpecialtyModel[];
  availability?: EmployeeAvailabilityModel[];

  static get relationMappings(): RelationMappings | RelationMappingsThunk {
    return {
      user: {
        relation: Model.BelongsToOneRelation,
        modelClass: UserModel,
        join: {
          from: 'employees.user_id',
          to: 'users.id',
        },
      },
      area: {
        relation: Model.BelongsToOneRelation,
        modelClass: AreaModel,
        join: {
          from: 'employees.area_id',
          to: 'areas.id',
        },
      },
      specialties: {
        relation: Model.ManyToManyRelation,
        modelClass: SpecialtyModel,
        join: {
          from: 'employees.id',
          through: {
            from: 'employee_specialties.employee_id',
            to: 'employee_specialties.specialty_id',
          },
          to: 'specialties.id',
        },
      },
      availability: {
        relation: Model.HasManyRelation,
        modelClass: EmployeeAvailabilityModel,
        join: {
          from: 'employees.id',
          to: 'employee_availability.employee_id',
        },
      },
    };
  }
}
