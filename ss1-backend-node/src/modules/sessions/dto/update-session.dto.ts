import {
  IsInt,
  IsOptional,
  IsString,
  IsDateString,
  IsBoolean,
} from 'class-validator';

export class UpdateSessionDto {
  @IsInt()
  @IsOptional()
  professional_id?: number;

  @IsDateString()
  @IsOptional()
  session_datetime?: string;

  @IsInt()
  @IsOptional()
  session_number?: number;

  @IsBoolean()
  @IsOptional()
  attended?: boolean;

  @IsString()
  @IsOptional()
  absence_reason?: string;

  @IsString()
  @IsOptional()
  topics?: string;

  @IsString()
  @IsOptional()
  interventions?: string;

  @IsString()
  @IsOptional()
  patient_response?: string;

  @IsString()
  @IsOptional()
  assigned_tasks?: string;

  @IsString()
  @IsOptional()
  observations?: string;

  @IsDateString()
  @IsOptional()
  next_appointment_datetime?: string;

  @IsString()
  @IsOptional()
  digital_signature_path?: string;

  @IsInt()
  @IsOptional()
  appointment_id?: number;
}
