import {
  IsArray,
  IsDateString,
  IsEmail,
  IsIn,
  IsInt,
  IsNumber,
  IsOptional,
  IsString,
  Max,
  MaxLength,
  Min,
  MinLength,
  ValidateNested,
} from 'class-validator';
import { Type } from 'class-transformer';
import { EmployeeAvailabilityDto } from './employee-availability.dto';

export class UpdateEmployeeDto {
  // Datos del usuario
  @IsEmail({}, { message: 'El email debe ser válido' })
  @IsOptional()
  email?: string;

  @IsString({ message: 'El username debe ser un texto' })
  @MinLength(3, { message: 'El username debe tener al menos 3 caracteres' })
  @MaxLength(100, { message: 'El username no puede exceder 100 caracteres' })
  @IsOptional()
  username?: string;

  @IsInt({ message: 'El role_id debe ser un número entero' })
  @Min(1, { message: 'El role_id debe ser mayor a 0' })
  @IsOptional()
  role_id?: number;

  // Datos del empleado
  @IsString({ message: 'El nombre debe ser un texto' })
  @MinLength(2, { message: 'El nombre debe tener al menos 2 caracteres' })
  @MaxLength(100, { message: 'El nombre no puede exceder 100 caracteres' })
  @IsOptional()
  first_name?: string;

  @IsString({ message: 'El apellido debe ser un texto' })
  @MinLength(2, { message: 'El apellido debe tener al menos 2 caracteres' })
  @MaxLength(100, { message: 'El apellido no puede exceder 100 caracteres' })
  @IsOptional()
  last_name?: string;

  @IsString({ message: 'El número de licencia debe ser un texto' })
  @MaxLength(100, {
    message: 'El número de licencia no puede exceder 100 caracteres',
  })
  @IsOptional()
  license_number?: string;

  @IsInt({ message: 'El area_id debe ser un número entero' })
  @Min(1, { message: 'El area_id debe ser mayor a 0' })
  @IsOptional()
  area_id?: number;

  @IsNumber({}, { message: 'El salario base debe ser un número' })
  @Min(0, { message: 'El salario base no puede ser negativo' })
  @Max(999999999.99, { message: 'El salario base excede el límite permitido' })
  @IsOptional()
  base_salary?: number;

  @IsNumber({}, { message: 'La tarifa por sesión debe ser un número' })
  @Min(0, { message: 'La tarifa por sesión no puede ser negativa' })
  @Max(999999999.99, {
    message: 'La tarifa por sesión excede el límite permitido',
  })
  @IsOptional()
  session_rate?: number;

  @IsNumber({}, { message: 'El porcentaje IGSS debe ser un número' })
  @Min(0, { message: 'El porcentaje IGSS no puede ser negativo' })
  @Max(100, { message: 'El porcentaje IGSS no puede exceder 100%' })
  @IsOptional()
  igss_percentage?: number;

  @IsDateString(
    {},
    {
      message:
        'La fecha de contratación debe ser una fecha válida (YYYY-MM-DD)',
    },
  )
  @IsOptional()
  hired_at?: string;

  @IsArray({ message: 'specialty_ids: Las especialidades deben ser un array' })
  @IsInt({
    each: true,
    message: 'specialty_ids: Cada ID de especialidad debe ser un número entero',
  })
  @Min(1, { each: true, message: 'specialty_ids: Cada ID debe ser mayor a 0' })
  @IsOptional()
  specialty_ids?: number[];

  @IsArray({ message: 'availability: La disponibilidad debe ser un array' })
  @ValidateNested({ each: true })
  @Type(() => EmployeeAvailabilityDto)
  @IsOptional()
  availability?: EmployeeAvailabilityDto[];
}
