import { IsNotEmpty, IsString, MaxLength, IsOptional } from 'class-validator';

export class CreateAreaDto {
  @IsString({ message: 'El nombre debe ser un texto' })
  @IsNotEmpty({ message: 'El nombre es obligatorio' })
  @MaxLength(120, { message: 'El nombre no puede exceder 120 caracteres' })
  name: string;

  @IsString({ message: 'La descripción debe ser un texto' })
  @IsNotEmpty({ message: 'La descripción es obligatoria' })
  @MaxLength(250, { message: 'La descripción no puede exceder 250 caracteres' })
  description: string;
}
