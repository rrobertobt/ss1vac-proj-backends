import { IsDateString, IsOptional, IsInt, Min } from 'class-validator';
import { Type } from 'class-transformer';

export class CheckAvailabilityDto {
  @IsDateString()
  date: string; // YYYY-MM-DD

  @IsOptional()
  @Type(() => Number)
  @IsInt()
  @Min(1)
  specialtyId?: number;

  @IsOptional()
  @Type(() => Number)
  @IsInt()
  @Min(1)
  professionalId?: number;
}
