import {
  Injectable,
  NotFoundException,
  BadRequestException,
  Inject,
} from '@nestjs/common';
import type { ModelClass } from 'objection';
import {
  PayrollPeriodModel,
  PayrollRecordModel,
} from './entities/payroll.entity';
import { EmployeeModel } from '../employees/entities/employee.entity';
import type { AppointmentModel } from '../appointments/entities/appointment.entity';
import { CreatePayrollPeriodDto } from './dto/create-period.dto';
import { UpdatePayrollRecordDto } from './dto/update-payroll-record.dto';

@Injectable()
export class PayrollService {
  constructor(
    @Inject('AppointmentModel')
    private appointmentModel: ModelClass<AppointmentModel>,
  ) {}

  // GET /payroll/periods
  async getPeriods() {
    const periods = await PayrollPeriodModel.query().orderBy(
      'period_start',
      'desc',
    );

    return periods;
  }

  // POST /payroll/periods
  async createPeriod(dto: CreatePayrollPeriodDto) {
    const period = await PayrollPeriodModel.query().insert({
      period_start: new Date(dto.period_start),
      period_end: new Date(dto.period_end),
      status: 'OPEN',
    });

    return period;
  }

  // POST /payroll/periods/:id/calculate
  async calculatePayroll(periodId: number) {
    // Verificar que el período exista
    const period = await PayrollPeriodModel.query().findById(periodId);
    if (!period) {
      throw new NotFoundException(`Period with ID ${periodId} not found`);
    }

    if (period.status !== 'OPEN') {
      throw new BadRequestException(`Period status must be OPEN to calculate`);
    }

    // Obtener todos los empleados activos
    const employees = await EmployeeModel.query().where('status', 'ACTIVE');

    const periodStart = new Date(period.period_start);
    const periodEnd = new Date(period.period_end);

    for (const employee of employees) {
      // A) Base salary
      const base_salary_amount = Number(employee.base_salary || 0);

      // B) Contar sesiones completadas en el período
      const appointments = await this.appointmentModel
        .query()
        .where('professional_id', employee.id)
        .where('status', 'COMPLETED')
        .whereBetween('start_datetime', [periodStart, periodEnd]);

      const sessions_count = appointments.length;

      // C) Calcular pago por sesiones
      const session_rate = Number(employee.session_rate || 0);
      const sessions_amount = sessions_count * session_rate;

      // Obtener el registro existente si hay uno
      const existingRecord = await PayrollRecordModel.query()
        .where('employee_id', employee.id)
        .where('period_id', periodId)
        .first();

      // Mantener bonuses y other_deductions si ya existen
      const bonuses_amount = existingRecord
        ? Number(existingRecord.bonuses_amount)
        : 0;
      const other_deductions = existingRecord
        ? Number(existingRecord.other_deductions)
        : 0;

      // D) Calcular IGSS
      const igss_percentage = Number(employee.igss_percentage || 0);
      const igss_deduction =
        (base_salary_amount + sessions_amount + bonuses_amount) *
        (igss_percentage / 100);

      // E) Calcular total
      const total_pay =
        base_salary_amount +
        sessions_amount +
        bonuses_amount -
        igss_deduction -
        other_deductions;

      // F) UPSERT
      const recordData = {
        employee_id: employee.id,
        period_id: periodId,
        base_salary_amount,
        sessions_count,
        sessions_amount,
        bonuses_amount,
        igss_deduction,
        other_deductions,
        total_pay,
        updated_at: new Date(),
      };

      if (existingRecord) {
        // UPDATE
        await PayrollRecordModel.query()
          .patch(recordData)
          .where('id', existingRecord.id);
      } else {
        // INSERT
        await PayrollRecordModel.query().insert({
          ...recordData,
          created_at: new Date(),
        });
      }
    }

    return {
      message: 'Payroll calculated successfully',
      employees_processed: employees.length,
    };
  }

  // GET /payroll/periods/:id/records
  async getPeriodRecords(periodId: number) {
    const period = await PayrollPeriodModel.query().findById(periodId);
    if (!period) {
      throw new NotFoundException(`Period with ID ${periodId} not found`);
    }

    const records = await PayrollRecordModel.query()
      .where('period_id', periodId)
      .withGraphFetched('employee.[user]')
      .joinRelated('employee')
      .orderBy('employee.last_name', 'asc');

    return {
      period,
      records,
    };
  }

  // GET /payroll/records/:id
  async getPayrollRecord(recordId: number) {
    const record = await PayrollRecordModel.query()
      .findById(recordId)
      .withGraphFetched('[employee.[user], period]');

    if (!record) {
      throw new NotFoundException(
        `Payroll record with ID ${recordId} not found`,
      );
    }

    return record;
  }

  // PATCH /payroll/records/:id
  async updatePayrollRecord(recordId: number, dto: UpdatePayrollRecordDto) {
    const record = await PayrollRecordModel.query().findById(recordId);
    if (!record) {
      throw new NotFoundException(
        `Payroll record with ID ${recordId} not found`,
      );
    }

    // Verificar que el período aún esté OPEN
    const period = await PayrollPeriodModel.query().findById(record.period_id);
    if (!period) {
      throw new NotFoundException('Period not found');
    }
    if (period.status !== 'OPEN') {
      throw new BadRequestException(
        'Cannot update records for a closed or paid period',
      );
    }

    // Obtener employee para recalcular IGSS
    const employee = await EmployeeModel.query().findById(record.employee_id);
    if (!employee) {
      throw new NotFoundException('Employee not found');
    }

    // Actualizar bonos o deducciones
    const bonuses_amount =
      dto.bonuses_amount !== undefined
        ? dto.bonuses_amount
        : record.bonuses_amount;
    const other_deductions =
      dto.other_deductions !== undefined
        ? dto.other_deductions
        : record.other_deductions;

    // Recalcular IGSS con los nuevos valores
    const igss_percentage = Number(employee.igss_percentage || 0);
    const igss_deduction =
      (Number(record.base_salary_amount) +
        Number(record.sessions_amount) +
        bonuses_amount) *
      (igss_percentage / 100);

    // Recalcular total
    const total_pay =
      Number(record.base_salary_amount) +
      Number(record.sessions_amount) +
      bonuses_amount -
      igss_deduction -
      other_deductions;

    const updatedRecord = await PayrollRecordModel.query()
      .patchAndFetchById(recordId, {
        bonuses_amount,
        other_deductions,
        igss_deduction,
        total_pay,
        updated_at: new Date(),
      })
      .withGraphFetched('[employee.[user], period]');

    return updatedRecord;
  }

  // POST /payroll/periods/:id/close
  async closePeriod(periodId: number) {
    const period = await PayrollPeriodModel.query().findById(periodId);
    if (!period) {
      throw new NotFoundException(`Period with ID ${periodId} not found`);
    }

    if (period.status !== 'OPEN') {
      throw new BadRequestException('Period is already closed or paid');
    }

    const updatedPeriod = await PayrollPeriodModel.query().patchAndFetchById(
      periodId,
      {
        status: 'CLOSED',
        updated_at: new Date(),
      },
    );

    return updatedPeriod;
  }

  // POST /payroll/periods/:id/pay
  async payPeriod(periodId: number) {
    const period = await PayrollPeriodModel.query().findById(periodId);
    if (!period) {
      throw new NotFoundException(`Period with ID ${periodId} not found`);
    }

    if (period.status !== 'CLOSED') {
      throw new BadRequestException('Period must be CLOSED before paying');
    }

    const now = new Date();

    // Actualizar el período a PAID
    const updatedPeriod = await PayrollPeriodModel.query().patchAndFetchById(
      periodId,
      {
        status: 'PAID',
        updated_at: now,
      },
    );

    // Marcar todos los records como pagados
    await PayrollRecordModel.query()
      .patch({ paid_at: now, updated_at: now })
      .where('period_id', periodId)
      .whereNull('paid_at');

    return updatedPeriod;
  }

  // GET /payroll/employees/:employeeId/history
  async getEmployeePayrollHistory(employeeId: number) {
    const employee = await EmployeeModel.query().findById(employeeId);
    if (!employee) {
      throw new NotFoundException(`Employee with ID ${employeeId} not found`);
    }

    const records = await PayrollRecordModel.query()
      .where('employee_id', employeeId)
      .withGraphFetched('period')
      .orderBy('period.period_start', 'desc');

    return {
      employee,
      records,
    };
  }
}
