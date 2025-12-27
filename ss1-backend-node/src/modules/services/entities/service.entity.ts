import { Model } from 'objection';

export class ServiceModel extends Model {
  static tableName = 'services';

  id: number;
  code: string;
  name: string;
  area_id: number | null;
  default_price: number;
  description: string | null;
  is_active: boolean;
  created_at: Date;
  updated_at: Date;
}
