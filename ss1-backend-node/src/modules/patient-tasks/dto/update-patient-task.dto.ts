import {
  IsString,
  IsOptional,
  IsDateString,
  MaxLength,
  IsIn,
} from 'class-validator';

export class UpdatePatientTaskDto {
  @IsString()
  @IsOptional()
  @MaxLength(200)
  title?: string;

  @IsString()
  @IsOptional()
  description?: string;

  @IsDateString()
  @IsOptional()
  due_date?: string;

  @IsString()
  @IsOptional()
  @IsIn(['PENDING', 'COMPLETED', 'CANCELLED'])
  status?: string;
}
