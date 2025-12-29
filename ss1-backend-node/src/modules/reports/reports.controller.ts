import {
  Controller,
  Get,
  Query,
  UseGuards,
  ValidationPipe,
} from '@nestjs/common';
import { ReportsService } from './reports.service';
import {
  RevenueReportDto,
  PayrollReportDto,
  SalesHistoryDto,
  PatientsPerSpecialtyDto,
} from './dto/reports.dto';
import { JwtAuthGuard } from 'src/core/auth/guards/jwt-auth.guard';
import { PermissionsGuard } from 'src/core/auth/guards/permissions.guard';
import { Permissions } from 'src/core/decorators/permissions.decorator';
import { Permission } from 'src/core/enums/permissions.enum';

@Controller('reports')
@UseGuards(JwtAuthGuard, PermissionsGuard)
export class ReportsController {
  constructor(private readonly reportsService: ReportsService) {}

  /**
   * GET /reports/revenue
   * Reporte de ingresos por período
   * Permisos: VIEW_REPORTS_FINANCIAL
   */
  @Get('revenue')
  @Permissions(Permission.VIEW_REPORTS_FINANCIAL)
  async getRevenueReport(
    @Query(new ValidationPipe({ transform: true })) dto: RevenueReportDto,
  ) {
    return this.reportsService.getRevenueReport(dto);
  }

  /**
   * GET /reports/payroll
   * Reporte de pagos realizados a empleados
   * Permisos: VIEW_REPORTS_HR
   */
  @Get('payroll')
  @Permissions(Permission.VIEW_REPORTS_HR)
  async getPayrollReport(
    @Query(new ValidationPipe({ transform: true })) dto: PayrollReportDto,
  ) {
    return this.reportsService.getPayrollReport(dto);
  }

  /**
   * GET /reports/sales
   * Historial de ventas
   * Permisos: VIEW_REPORTS_FINANCIAL
   */
  @Get('sales')
  @Permissions(Permission.VIEW_REPORTS_FINANCIAL)
  async getSalesHistory(
    @Query(new ValidationPipe({ transform: true })) dto: SalesHistoryDto,
  ) {
    return this.reportsService.getSalesHistory(dto);
  }

  /**
   * GET /reports/patients-per-specialty
   * Pacientes atendidos por especialidad (área)
   * Permisos: VIEW_REPORTS_CLINICAL
   */
  @Get('patients-per-specialty')
  @Permissions(Permission.VIEW_REPORTS_CLINICAL)
  async getPatientsPerSpecialty(
    @Query(new ValidationPipe({ transform: true }))
    dto: PatientsPerSpecialtyDto,
  ) {
    return this.reportsService.getPatientsPerSpecialty(dto);
  }
}
