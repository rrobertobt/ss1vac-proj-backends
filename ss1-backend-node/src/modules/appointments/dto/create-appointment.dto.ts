import {
  IsInt,
  IsOptional,
  IsDateString,
  IsString,
  MaxLength,
  Min,
} from 'class-validator';

export class CreateAppointmentDto {
  @IsInt()
  @Min(1)
  patient_id: number;

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

  @IsDateString()
  start_datetime: string; // ISO 8601 format

  @IsDateString()
  end_datetime: string; // ISO 8601 format

  @IsOptional()
  @IsString()
  notes?: string;
}
