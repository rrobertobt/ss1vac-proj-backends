import {
  IsEmail,
  IsNotEmpty,
  IsString,
  IsInt,
  IsNumber,
  IsOptional,
  IsDateString,
  Min,
  Max,
  MinLength,
  MaxLength,
  IsIn,
  Matches,
} from 'class-validator';

const EMPLOYEE_TYPES = [
  'PSYCHOLOGIST',
  'PSYCHIATRIST',
  'TECHNICIAN',
  'MAINTENANCE',
  'ADMIN_STAFF',
] as const;

export class CreateEmployeeDto {
  // Datos del usuario
  @IsEmail({}, { message: 'El email debe ser válido' })
  @IsNotEmpty({ message: 'El email es obligatorio' })
  email: string;

  @IsString({ message: 'El username debe ser un texto' })
  @MinLength(3, { message: 'El username debe tener al menos 3 caracteres' })
  @MaxLength(100, { message: 'El username no puede exceder 100 caracteres' })
  @IsOptional()
  username?: string;

  @IsInt({ message: 'El role_id debe ser un número entero' })
  @Min(1, { message: 'El role_id debe ser mayor a 0' })
  @IsNotEmpty({ message: 'El role_id es obligatorio' })
  role_id: number;

  // Datos del empleado
  @IsString({ message: 'El nombre debe ser un texto' })
  @MinLength(2, { message: 'El nombre debe tener al menos 2 caracteres' })
  @MaxLength(100, { message: 'El nombre no puede exceder 100 caracteres' })
  @IsNotEmpty({ message: 'El nombre es obligatorio' })
  first_name: string;

  @IsString({ message: 'El apellido debe ser un texto' })
  @MinLength(2, { message: 'El apellido debe tener al menos 2 caracteres' })
  @MaxLength(100, { message: 'El apellido no puede exceder 100 caracteres' })
  @IsNotEmpty({ message: 'El apellido es obligatorio' })
  last_name: string;

  @IsString({ message: 'El tipo de empleado debe ser un texto' })
  @IsIn(EMPLOYEE_TYPES, {
    message: `El tipo de empleado debe ser uno de: ${EMPLOYEE_TYPES.join(', ')}`,
  })
  @IsNotEmpty({ message: 'El tipo de empleado es obligatorio' })
  employee_type: string;

  @IsString({ message: 'El número de licencia debe ser un texto' })
  @MaxLength(100, { message: 'El número de licencia no puede exceder 100 caracteres' })
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
  @Max(999999999.99, { message: 'La tarifa por sesión excede el límite permitido' })
  @IsOptional()
  session_rate?: number;

  @IsNumber({}, { message: 'El porcentaje IGSS debe ser un número' })
  @Min(0, { message: 'El porcentaje IGSS no puede ser negativo' })
  @Max(100, { message: 'El porcentaje IGSS no puede exceder 100%' })
  @IsOptional()
  igss_percentage?: number;

  @IsDateString({}, { message: 'La fecha de contratación debe ser una fecha válida (YYYY-MM-DD)' })
  @IsOptional()
  hired_at?: string;
}
