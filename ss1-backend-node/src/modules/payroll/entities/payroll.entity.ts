import { Model, RelationMappings, RelationMappingsThunk } from 'objection';
import { EmployeeModel } from '../../employees/entities/employee.entity';

export class PayrollPeriodModel extends Model {
  static tableName = 'payroll_periods';

  id: number;
  period_start: Date;
  period_end: Date;
  status: string; // OPEN, CLOSED, PAID
  created_at: Date;
  updated_at: Date;

  // Relaciones
  records?: PayrollRecordModel[];

  static get relationMappings(): RelationMappings | RelationMappingsThunk {
    return {
      records: {
        relation: Model.HasManyRelation,
        modelClass: PayrollRecordModel,
        join: {
          from: 'payroll_periods.id',
          to: 'payroll_records.period_id',
        },
      },
    };
  }
}

export class PayrollRecordModel extends Model {
  static tableName = 'payroll_records';

  id: number;
  employee_id: number;
  period_id: number;
  base_salary_amount: number;
  sessions_count: number;
  sessions_amount: number;
  bonuses_amount: number;
  igss_deduction: number;
  other_deductions: number;
  total_pay: number;
  paid_at: Date | null;
  created_at: Date;
  updated_at: Date;

  // Relaciones
  employee?: EmployeeModel;
  period?: PayrollPeriodModel;

  static get relationMappings(): RelationMappings | RelationMappingsThunk {
    return {
      employee: {
        relation: Model.BelongsToOneRelation,
        modelClass: EmployeeModel,
        join: {
          from: 'payroll_records.employee_id',
          to: 'employees.id',
        },
      },
      period: {
        relation: Model.BelongsToOneRelation,
        modelClass: PayrollPeriodModel,
        join: {
          from: 'payroll_records.period_id',
          to: 'payroll_periods.id',
        },
      },
    };
  }
}
