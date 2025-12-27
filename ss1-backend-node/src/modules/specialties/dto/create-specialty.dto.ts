import { IsNotEmpty, IsString, MaxLength, IsOptional } from 'class-validator';

export class CreateSpecialtyDto {
  @IsString({ message: 'El nombre debe ser un texto' })
  @IsNotEmpty({ message: 'El nombre es obligatorio' })
  @MaxLength(120, { message: 'El nombre no puede exceder 120 caracteres' })
  name: string;

  @IsString({ message: 'La descripción debe ser un texto' })
  @IsOptional()
  description?: string;
}
