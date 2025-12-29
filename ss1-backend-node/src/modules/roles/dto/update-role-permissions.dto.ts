import { IsArray, IsInt, ArrayNotEmpty } from 'class-validator';

export class UpdateRolePermissionsDto {
  @IsArray({ message: 'Los IDs de permisos deben ser un arreglo' })
  @ArrayNotEmpty({ message: 'Debe proporcionar al menos un permiso' })
  @IsInt({ each: true, message: 'Cada ID de permiso debe ser un número entero' })
  permission_ids: number[];
}
