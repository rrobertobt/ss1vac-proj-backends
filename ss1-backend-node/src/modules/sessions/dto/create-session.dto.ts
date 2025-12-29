import {
  IsInt,
  IsNotEmpty,
  IsOptional,
  IsString,
  IsDateString,
  IsBoolean,
} from 'class-validator';

export class CreateSessionDto {
  @IsInt()
  @IsOptional()
  professional_id?: number;

  @IsDateString()
  @IsNotEmpty()
  session_datetime: string;

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

  @IsInt()
  @IsOptional()
  appointment_id?: number;
}
