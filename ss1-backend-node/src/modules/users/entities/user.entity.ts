import { Model, RelationMappings, RelationMappingsThunk } from 'objection';
import { RoleModel } from 'src/modules/roles/entities/role.entity';
import { EmployeeModel } from 'src/modules/employees/entities/employee.entity';
import { PatientModel } from 'src/modules/patients/entities/patient.entity';

export class UserModel extends Model {
  static tableName = 'users';

  id: number;
  email: string;
  username: string;
  password_hash?: string;
  role_id: number;
  is_active: boolean;
  last_login_at: Date | null;
  two_fa_enabled: boolean;
  two_fa_secret: string | null;
  two_fa_expires_at: Date | null;
  two_fa_attempts: number | null;
  password_reset_token: string | null;
  password_reset_expires: Date | null;
  created_at: Date;
  updated_at: Date;

  // Relaciones
  role?: RoleModel;
  employee?: EmployeeModel;
  patient?: PatientModel;

  static get relationMappings(): RelationMappings | RelationMappingsThunk {
    return {
      role: {
        relation: Model.BelongsToOneRelation,
        modelClass: RoleModel,
        join: {
          from: 'users.role_id',
          to: 'roles.id',
        },
      },
      employee: {
        relation: Model.HasOneRelation,
        modelClass: EmployeeModel,
        join: {
          from: 'users.id',
          to: 'employees.user_id',
        },
      },
      patient: {
        relation: Model.HasOneRelation,
        modelClass: PatientModel,
        join: {
          from: 'users.id',
          to: 'patients.user_id',
        },
      },
    };
  }
}
