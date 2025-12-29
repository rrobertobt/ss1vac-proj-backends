import { IsNumber, IsOptional, Min } from 'class-validator';

export class UpdatePayrollRecordDto {
  @IsOptional()
  @IsNumber()
  @Min(0)
  bonuses_amount?: number;

  @IsOptional()
  @IsNumber()
  @Min(0)
  other_deductions?: number;
}
