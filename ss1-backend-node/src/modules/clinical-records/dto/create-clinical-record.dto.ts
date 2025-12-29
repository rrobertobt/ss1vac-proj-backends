import {
  IsInt,
  IsNotEmpty,
  IsOptional,
  IsString,
  IsDateString,
  MaxLength,
} from 'class-validator';

export class CreateClinicalRecordDto {
  @IsInt()
  @IsNotEmpty()
  patient_id: number;

  @IsString()
  @IsOptional()
  @MaxLength(50)
  record_number?: string;

  @IsString()
  @IsOptional()
  @MaxLength(150)
  institution_name?: string;

  @IsString()
  @IsOptional()
  @MaxLength(120)
  service?: string;

  @IsDateString()
  @IsOptional()
  opening_date?: string;

  @IsInt()
  @IsOptional()
  responsible_employee_id?: number;

  @IsString()
  @IsOptional()
  @MaxLength(100)
  responsible_license?: string;

  @IsString()
  @IsOptional()
  @MaxLength(150)
  referral_source?: string;

  @IsString()
  @IsOptional()
  chief_complaint?: string;
}
