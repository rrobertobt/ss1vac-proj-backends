import { Model, RelationMappings, RelationMappingsThunk } from 'objection';
import { AreaModel } from '../../areas/entities/area.entity';

export class ProductModel extends Model {
  static tableName = 'products';

  id: number;
  sku: string | null;
  name: string;
  description: string | null;
  product_type: string; // MEDICATION, TOOL, OTHER
  unit: string | null;
  cost_price: number;
  sale_price: number;
  min_stock: number;
  current_stock: number;
  is_active: boolean;
  created_at: Date;
  updated_at: Date;
}
