import {
  Controller,
  Post,
  Get,
  Patch,
  Body,
  Param,
  ParseIntPipe,
  UseGuards,
  ValidationPipe,
} from '@nestjs/common';
import { PayrollService } from './payroll.service';
import { CreatePayrollPeriodDto } from './dto/create-period.dto';
import { UpdatePayrollRecordDto } from './dto/update-payroll-record.dto';
import { JwtAuthGuard } from 'src/core/auth/guards/jwt-auth.guard';
import { PermissionsGuard } from 'src/core/auth/guards/permissions.guard';
import { Permissions } from 'src/core/decorators/permissions.decorator';
import { Permission } from 'src/core/enums/permissions.enum';

@Controller('payroll')
@UseGuards(JwtAuthGuard, PermissionsGuard)
export class PayrollController {
  constructor(private readonly payrollService: PayrollService) {}

  /**
   * GET /payroll/periods
   * Obtener todos los períodos de nómina
   */
  @Get('periods')
  @Permissions(Permission.VIEW_PAYROLL, Permission.MANAGE_PAYROLL)
  async getPeriods() {
    return this.payrollService.getPeriods();
  }

  /**
   * POST /payroll/periods
   * Crear un nuevo período de nómina
   */
  @Post('periods')
  @Permissions(Permission.MANAGE_PAYROLL)
  async createPeriod(@Body(ValidationPipe) dto: CreatePayrollPeriodDto) {
    return this.payrollService.createPeriod(dto);
  }

  /**
   * POST /payroll/periods/:id/calculate
   * Calcular la nómina para todos los empleados activos en el período
   */
  @Post('periods/:id/calculate')
  @Permissions(Permission.MANAGE_PAYROLL)
  async calculatePayroll(@Param('id', ParseIntPipe) periodId: number) {
    return this.payrollService.calculatePayroll(periodId);
  }

  /**
   * GET /payroll/periods/:id/records
   * Obtener todos los registros de nómina de un período
   */
  @Get('periods/:id/records')
  @Permissions(Permission.VIEW_PAYROLL, Permission.MANAGE_PAYROLL)
  async getPeriodRecords(@Param('id', ParseIntPipe) periodId: number) {
    return this.payrollService.getPeriodRecords(periodId);
  }

  /**
   * GET /payroll/records/:id
   * Obtener el detalle de un registro de nómina específico
   */
  @Get('records/:id')
  @Permissions(Permission.VIEW_PAYROLL, Permission.MANAGE_PAYROLL)
  async getPayrollRecord(@Param('id', ParseIntPipe) recordId: number) {
    return this.payrollService.getPayrollRecord(recordId);
  }

  /**
   * PATCH /payroll/records/:id
   * Actualizar bonos o deducciones de un registro de nómina
   */
  @Patch('records/:id')
  @Permissions(Permission.MANAGE_PAYROLL)
  async updatePayrollRecord(
    @Param('id', ParseIntPipe) recordId: number,
    @Body(ValidationPipe) dto: UpdatePayrollRecordDto,
  ) {
    return this.payrollService.updatePayrollRecord(recordId, dto);
  }

  /**
   * POST /payroll/periods/:id/close
   * Cerrar un período de nómina (cambiar status a CLOSED)
   */
  @Post('periods/:id/close')
  @Permissions(Permission.MANAGE_PAYROLL)
  closePeriod(@Param('id', ParseIntPipe) periodId: number) {
    return this.payrollService.closePeriod(periodId);
  }

  /**
   * POST /payroll/periods/:id/pay
   * Marcar un período como pagado (cambiar status a PAID)
   */
  @Post('periods/:id/pay')
  @Permissions(Permission.MANAGE_PAYROLL)
  payPeriod(@Param('id', ParseIntPipe) periodId: number) {
    return this.payrollService.payPeriod(periodId);
  }

  /**
   * GET /payroll/employees/:employeeId/history
   * Obtener el historial de nómina de un empleado
   */
  @Get('employees/:employeeId/history')
  @Permissions(Permission.VIEW_PAYROLL, Permission.MANAGE_PAYROLL)
  getEmployeePayrollHistory(
    @Param('employeeId', ParseIntPipe) employeeId: number,
  ) {
    return this.payrollService.getEmployeePayrollHistory(employeeId);
  }
}
