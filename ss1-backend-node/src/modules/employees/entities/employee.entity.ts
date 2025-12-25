import { Model } from 'objection';

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
}
