import {
  IsOptional,
  IsString,
  MinLength,
  MaxLength,
  IsEmail,
} from 'class-validator';

export class UpdateProfileDto {
  // Usuario (tabla users)
  @IsOptional()
  @IsString()
  @MinLength(3, { message: 'El username debe tener al menos 3 caracteres' })
  @MaxLength(100, { message: 'El username no puede exceder 100 caracteres' })
  username?: string;

  // Datos personales de paciente (solo aplicable si el usuario es paciente)
  @IsOptional()
  @IsString()
  @MaxLength(50, { message: 'El teléfono no puede exceder 50 caracteres' })
  phone?: string;

  @IsOptional()
  @IsEmail({}, { message: 'Debe ser un email válido' })
  @MaxLength(255, { message: 'El email no puede exceder 255 caracteres' })
  email?: string;

  @IsOptional()
  @IsString()
  address?: string;

  @IsOptional()
  @IsString()
  @MaxLength(20, { message: 'El género no puede exceder 20 caracteres' })
  gender?: string;

  @IsOptional()
  @IsString()
  @MaxLength(30, { message: 'El estado civil no puede exceder 30 caracteres' })
  marital_status?: string;

  @IsOptional()
  @IsString()
  @MaxLength(120, { message: 'La ocupación no puede exceder 120 caracteres' })
  occupation?: string;

  @IsOptional()
  @IsString()
  @MaxLength(120, {
    message: 'El nivel de educación no puede exceder 120 caracteres',
  })
  education_level?: string;

  @IsOptional()
  @IsString()
  @MaxLength(150, {
    message:
      'El nombre del contacto de emergencia no puede exceder 150 caracteres',
  })
  emergency_contact_name?: string;

  @IsOptional()
  @IsString()
  @MaxLength(80, {
    message:
      'La relación del contacto de emergencia no puede exceder 80 caracteres',
  })
  emergency_contact_relationship?: string;

  @IsOptional()
  @IsString()
  @MaxLength(50, {
    message:
      'El teléfono del contacto de emergencia no puede exceder 50 caracteres',
  })
  emergency_contact_phone?: string;
}
