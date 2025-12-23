import { Model } from 'objection';

export class PermissionModel extends Model {
  static tableName = 'permissions';

  id: number;
  code: string;
  description: string | null;
  created_at: Date;
  updated_at: Date;
}
