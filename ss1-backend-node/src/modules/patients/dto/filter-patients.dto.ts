import { IsOptional, IsString, IsInt, Min, IsIn } from 'class-validator';
import { Type } from 'class-transformer';

const PATIENT_STATUSES = ['ACTIVE', 'INACTIVE'] as const;

export class FilterPatientsDto {
  @IsOptional()
  @IsString({ message: 'El término de búsqueda debe ser un texto' })
  search?: string;

  @IsOptional()
  @IsInt({ message: 'La página debe ser un número entero' })
  @Min(1, { message: 'La página debe ser mayor o igual a 1' })
  @Type(() => Number)
  page?: number = 1;

  @IsOptional()
  @IsInt({ message: 'El límite debe ser un número entero' })
  @Min(1, { message: 'El límite debe ser mayor o igual a 1' })
  @Type(() => Number)
  limit?: number = 10;

  @IsOptional()
  @IsString({ message: 'El estado debe ser un texto' })
  @IsIn(PATIENT_STATUSES, {
    message: `El estado debe ser uno de: ${PATIENT_STATUSES.join(', ')}`,
  })
  status?: string;
}
