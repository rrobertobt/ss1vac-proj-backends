import {
  IsOptional,
  IsInt,
  IsDateString,
  IsString,
  MaxLength,
  Min,
} from 'class-validator';

export class UpdateAppointmentDto {
  @IsOptional()
  @IsInt()
  @Min(1)
  professional_id?: number;

  @IsOptional()
  @IsInt()
  @Min(1)
  specialty_id?: number;

  @IsOptional()
  @IsString()
  @MaxLength(50)
  appointment_type?: string;

  @IsOptional()
  @IsDateString()
  start_datetime?: string;

  @IsOptional()
  @IsDateString()
  end_datetime?: string;

  @IsOptional()
  @IsString()
  notes?: string;
}
