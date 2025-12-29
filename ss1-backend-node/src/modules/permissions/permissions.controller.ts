import { Controller, Get, UseGuards } from '@nestjs/common';
import { PermissionsService } from './permissions.service';
import { JwtAuthGuard } from 'src/core/auth/guards/jwt-auth.guard';

@Controller('permissions')
@UseGuards(JwtAuthGuard)
export class PermissionsController {
  constructor(private readonly permissionsService: PermissionsService) {}

  /**
   * Listar todos los permisos disponibles.
   * Requiere autenticación pero no permisos específicos.
   */
  @Get()
  findAll() {
    return this.permissionsService.findAll();
  }
}
