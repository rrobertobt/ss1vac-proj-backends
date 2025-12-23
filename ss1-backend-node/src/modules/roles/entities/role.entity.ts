import { Model, RelationMappings, RelationMappingsThunk } from 'objection';
import { UserModel } from 'src/modules/users/entities/user.entity';
import { PermissionModel } from 'src/modules/permissions/entities/permission.entity';

export class RoleModel extends Model {
  static tableName = 'roles';

  id: number;
  name: string;
  label: string;
  description: string | null;
  created_at: Date;
  updated_at: Date;

  // Relaciones
  permissions?: PermissionModel[];

  static get relationMappings(): RelationMappings | RelationMappingsThunk {
    return {
      users: {
        relation: Model.HasManyRelation,
        modelClass: UserModel,
        join: {
          from: 'roles.id',
          to: 'users.role_id',
        },
      },
      permissions: {
        relation: Model.ManyToManyRelation,
        modelClass: PermissionModel,
        join: {
          from: 'roles.id',
          through: {
            from: 'role_permissions.role_id',
            to: 'role_permissions.permission_id',
          },
          to: 'permissions.id',
        },
      },
    };
  }
}
