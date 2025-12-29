import { IsOptional, IsDateString, IsInt, IsIn, Min } from 'class-validator';
import { Type } from 'class-transformer';

export class FilterAppointmentsDto {
  @IsOptional()
  @IsDateString()
  from?: string; // YYYY-MM-DD

  @IsOptional()
  @IsDateString()
  to?: string; // YYYY-MM-DD

  @IsOptional()
  @Type(() => Number)
  @IsInt()
  @Min(1)
  professionalId?: number;

  @IsOptional()
  @Type(() => Number)
  @IsInt()
  @Min(1)
  patientId?: number;

  @IsOptional()
  @IsIn(['SCHEDULED', 'COMPLETED', 'CANCELLED', 'NO_SHOW'])
  status?: string;

  @IsOptional()
  @Type(() => Number)
  @IsInt()
  @Min(1)
  page?: number = 1;

  @IsOptional()
  @Type(() => Number)
  @IsInt()
  @Min(1)
  limit?: number = 20;
}
