import { IsDateString, IsOptional } from 'class-validator';

export class ReportPeriodDto {
  @IsDateString()
  start_date: string;

  @IsDateString()
  end_date: string;
}

export class RevenueReportDto extends ReportPeriodDto {
  @IsOptional()
  currency?: string;
}

export class PayrollReportDto extends ReportPeriodDto {
  @IsOptional()
  employee_id?: number;
}

export class SalesHistoryDto extends ReportPeriodDto {
  @IsOptional()
  patient_id?: number;
}

export class PatientsPerSpecialtyDto extends ReportPeriodDto {
  @IsOptional()
  specialty_id?: number;

  @IsOptional()
  area_id?: number;
}
