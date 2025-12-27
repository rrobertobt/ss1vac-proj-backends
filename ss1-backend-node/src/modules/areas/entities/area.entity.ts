import { Model } from 'objection';

export class AreaModel extends Model {
  static tableName = 'areas';

  id: number;
  name: string;
  description: string | null;
  created_at: Date;
  updated_at: Date;
}
