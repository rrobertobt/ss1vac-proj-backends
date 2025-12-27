import { IsString, MaxLength, IsOptional } from 'class-validator';

export class UpdateSpecialtyDto {
  @IsString({ message: 'El nombre debe ser un texto' })
  @MaxLength(120, { message: 'El nombre no puede exceder 120 caracteres' })
  @IsOptional()
  name?: string;

  @IsString({ message: 'La descripción debe ser un texto' })
  @IsOptional()
  description?: string;
}
