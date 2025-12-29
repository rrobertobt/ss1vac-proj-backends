import {
  IsEmail,
  IsString,
  IsOptional,
  IsDateString,
  MaxLength,
  IsIn,
  Matches,
} from 'class-validator';

const GENDERS = ['MALE', 'FEMALE', 'OTHER'] as const;
const MARITAL_STATUSES = [
  'SINGLE',
  'MARRIED',
  'DIVORCED',
  'WIDOWED',
  'DOMESTIC_PARTNERSHIP',
] as const;

export class UpdatePatientDto {
  @IsDateString(
    {},
    {
      message: 'La fecha de nacimiento debe ser una fecha válida (YYYY-MM-DD)',
    },
  )
  @IsOptional()
  dob?: string;

  @IsString({ message: 'El género debe ser un texto' })
  @IsIn(GENDERS, {
    message: `El género debe ser uno de: ${GENDERS.join(', ')}`,
  })
  @IsOptional()
  gender?: string;

  @IsString({ message: 'El estado civil debe ser un texto' })
  @IsIn(MARITAL_STATUSES, {
    message: `El estado civil debe ser uno de: ${MARITAL_STATUSES.join(', ')}`,
  })
  @IsOptional()
  marital_status?: string;

  @IsString({ message: 'La ocupación debe ser un texto' })
  @MaxLength(120, { message: 'La ocupación no puede exceder 120 caracteres' })
  @IsOptional()
  occupation?: string;

  @IsString({ message: 'El nivel educativo debe ser un texto' })
  @MaxLength(120, {
    message: 'El nivel educativo no puede exceder 120 caracteres',
  })
  @IsOptional()
  education_level?: string;

  @IsString({ message: 'La dirección debe ser un texto' })
  @MaxLength(500, { message: 'La dirección no puede exceder 500 caracteres' })
  @IsOptional()
  address?: string;

  @IsString({ message: 'El teléfono debe ser un texto' })
  @Matches(
    /^[+]?[(]?[0-9]{1,4}[)]?[-\s.]?[(]?[0-9]{1,4}[)]?[-\s.]?[0-9]{1,9}$/,
    {
      message: 'El teléfono debe tener un formato válido',
    },
  )
  @MaxLength(50, { message: 'El teléfono no puede exceder 50 caracteres' })
  @IsOptional()
  phone?: string;

  @IsEmail({}, { message: 'El email del paciente debe ser válido' })
  @IsOptional()
  email?: string;

  @IsString({
    message: 'El nombre del contacto de emergencia debe ser un texto',
  })
  @MaxLength(150, {
    message: 'El nombre del contacto no puede exceder 150 caracteres',
  })
  @IsOptional()
  emergency_contact_name?: string;

  @IsString({
    message: 'La relación del contacto de emergencia debe ser un texto',
  })
  @MaxLength(80, {
    message: 'La relación del contacto no puede exceder 80 caracteres',
  })
  @IsOptional()
  emergency_contact_relationship?: string;

  @IsString({
    message: 'El teléfono del contacto de emergencia debe ser un texto',
  })
  @Matches(
    /^[+]?[(]?[0-9]{1,4}[)]?[-\s.]?[(]?[0-9]{1,4}[)]?[-\s.]?[0-9]{1,9}$/,
    {
      message: 'El teléfono del contacto debe tener un formato válido',
    },
  )
  @MaxLength(50, {
    message: 'El teléfono del contacto no puede exceder 50 caracteres',
  })
  @IsOptional()
  emergency_contact_phone?: string;
}
