import { Model } from 'objection';

export class SpecialtyModel extends Model {
  static tableName = 'specialties';

  id: number;
  name: string;
  description: string | null;
  created_at: Date;
  updated_at: Date;
}
