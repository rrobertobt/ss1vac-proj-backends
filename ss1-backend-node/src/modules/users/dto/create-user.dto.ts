import {
  IsEmail,
  IsNotEmpty,
  IsString,
  IsInt,
  IsBoolean,
  IsOptional,
  MinLength,
  MaxLength,
  Min,
} from 'class-validator';

export class CreateUserDto {
  @IsEmail({}, { message: 'El email debe ser válido' })
  @IsNotEmpty({ message: 'El email es obligatorio' })
  email: string;

  @IsString({ message: 'El username debe ser un texto' })
  @MinLength(3, { message: 'El username debe tener al menos 3 caracteres' })
  @MaxLength(100, { message: 'El username no puede exceder 100 caracteres' })
  @IsOptional()
  username?: string;

  @IsString({ message: 'La contraseña debe ser un texto' })
  @MinLength(8, { message: 'La contraseña debe tener al menos 8 caracteres' })
  @MaxLength(100, { message: 'La contraseña no puede exceder 100 caracteres' })
  @IsOptional()
  password?: string;

  @IsInt({ message: 'El role_id debe ser un número entero' })
  @Min(1, { message: 'El role_id debe ser mayor a 0' })
  @IsNotEmpty({ message: 'El role_id es obligatorio' })
  role_id: number;

  @IsBoolean({ message: 'is_active debe ser un valor booleano' })
  @IsOptional()
  is_active?: boolean;
}
