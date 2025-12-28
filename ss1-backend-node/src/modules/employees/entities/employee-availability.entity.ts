import { Model } from 'objection';

export class EmployeeAvailabilityModel extends Model {
  static tableName = 'employee_availability';

  id!: number;
  employee_id!: number;
  day_of_week!: number;
  start_time!: string;
  end_time!: string;
  specialty_id!: number | null;
  is_active!: boolean;
  created_at!: Date;
  updated_at!: Date;
}
