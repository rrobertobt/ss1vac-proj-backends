import { IsOptional, IsInt, IsString, IsIn } from 'class-validator';
import { Type } from 'class-transformer';

export class FilterClinicalRecordsDto {
  @IsOptional()
  @IsInt()
  @Type(() => Number)
  patientId?: number;

  @IsOptional()
  @IsInt()
  @Type(() => Number)
  professionalId?: number;

  @IsOptional()
  @IsString()
  @IsIn(['ACTIVE', 'CLOSED'])
  status?: string;

  @IsOptional()
  @IsInt()
  @Type(() => Number)
  page?: number;

  @IsOptional()
  @IsInt()
  @Type(() => Number)
  limit?: number;
}
