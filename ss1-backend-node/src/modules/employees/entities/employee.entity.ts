import { Model, RelationMappings, RelationMappingsThunk } from 'objection';
import { UserModel } from 'src/modules/users/entities/user.entity';

export class EmployeeModel extends Model {
  static tableName = 'employees';

  id: number;
  user_id: number | null;
  first_name: string;
  last_name: string;
  employee_type: string;
  license_number: string | null;
  area_id: number | null;
  base_salary: number;
  session_rate: number;
  igss_percentage: number;
  hired_at: Date | null;
  status: string;
  created_at: Date;
  updated_at: Date;

  // Relación
  user?: UserModel;

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
    };
  }
}
