import {
  IsInt,
  IsNotEmpty,
  IsOptional,
  IsString,
  Matches,
  Max,
  Min,
} from 'class-validator';

export class EmployeeAvailabilityDto {
  @IsInt({ message: 'day_of_week: El día de la semana debe ser un número entero' })
  @Min(0, { message: 'day_of_week: El día debe estar entre 0 (Domingo) y 6 (Sábado)' })
  @Max(6, { message: 'day_of_week: El día debe estar entre 0 (Domingo) y 6 (Sábado)' })
  @IsNotEmpty({ message: 'day_of_week: El día de la semana es obligatorio' })
  day_of_week: number;

  @IsString({ message: 'start_time: La hora de inicio debe ser un texto' })
  @Matches(/^([01]\d|2[0-3]):([0-5]\d)$/, {
    message: 'start_time: La hora de inicio debe tener el formato HH:mm (ej: 09:00)',
  })
  @IsNotEmpty({ message: 'start_time: La hora de inicio es obligatoria' })
  start_time: string;

  @IsString({ message: 'end_time: La hora de fin debe ser un texto' })
  @Matches(/^([01]\d|2[0-3]):([0-5]\d)$/, {
    message: 'end_time: La hora de fin debe tener el formato HH:mm (ej: 17:00)',
  })
  @IsNotEmpty({ message: 'end_time: La hora de fin es obligatoria' })
  end_time: string;

  @IsInt({ message: 'specialty_id: El ID de la especialidad debe ser un número entero' })
  @Min(1, { message: 'specialty_id: El ID de la especialidad debe ser mayor a 0' })
  @IsOptional()
  specialty_id?: number;
}
