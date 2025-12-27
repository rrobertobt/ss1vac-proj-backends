import {
  IsEmail,
  IsString,
  IsInt,
  IsBoolean,
  IsOptional,
  MinLength,
  MaxLength,
  Min,
} from 'class-validator';

export class UpdateUserDto {
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

  @IsBoolean({ message: 'is_active debe ser un valor booleano' })
  @IsOptional()
  is_active?: boolean;

  @IsOptional()
  last_login_at?: Date | null;
}
