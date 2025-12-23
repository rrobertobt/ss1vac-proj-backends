import { Model, RelationMappings, RelationMappingsThunk } from 'objection';
import { UserModel } from 'src/modules/users/entities/user.entity';

export class RoleModel extends Model {
  static tableName = 'roles';

  id: number;
  name: string;
  label: string;
  description: string | null;
  created_at: Date;
  updated_at: Date;

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
    };
  }
}
