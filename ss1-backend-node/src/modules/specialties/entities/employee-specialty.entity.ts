import { Model } from 'objection';

export class EmployeeSpecialtyModel extends Model {
  static tableName = 'employee_specialties';

  employee_id: number;
  specialty_id: number;
}
