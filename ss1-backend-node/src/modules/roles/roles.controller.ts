import {
  Controller,
  Get,
  Post,
  Body,
  Patch,
  Param,
  Delete,
  Put,
  UseGuards,
  ParseIntPipe,
} from '@nestjs/common';
import { RolesService } from './roles.service';
import { CreateRoleDto } from './dto/create-role.dto';
import { UpdateRoleDto } from './dto/update-role.dto';
import { UpdateRolePermissionsDto } from './dto/update-role-permissions.dto';
import { JwtAuthGuard } from 'src/core/auth/guards/jwt-auth.guard';
import { PermissionsGuard } from 'src/core/auth/guards/permissions.guard';
import { Permissions } from 'src/core/decorators/permissions.decorator';
import { Permission } from 'src/core/enums/permissions.enum';

@Controller('roles')
export class RolesController {
  constructor(private readonly rolesService: RolesService) {}

  @Post()
  create(@Body() createRoleDto: CreateRoleDto) {
    return this.rolesService.create(createRoleDto);
  }

  /**
   * Listar todos los roles disponibles.
   * Requiere autenticación pero no permisos específicos.
   */
  @Get()
  @UseGuards(JwtAuthGuard)
  findAll() {
    return this.rolesService.findAll();
  }

  @Get(':id')
  @UseGuards(JwtAuthGuard)
  findOne(@Param('id', ParseIntPipe) id: number) {
    return this.rolesService.findOne(id);
  }

  /**
   * Obtener permisos de un rol específico.
   * Requiere permiso: MANAGE_ROLES o ASSIGN_ROLE_PERMISSIONS
   */
  @Get(':id/permissions')
  @UseGuards(JwtAuthGuard, PermissionsGuard)
  @Permissions(Permission.ASSIGN_ROLE_PERMISSIONS)
  getRolePermissions(@Param('id', ParseIntPipe) id: number) {
    return this.rolesService.getRolePermissions(id);
  }

  /**
   * Actualizar permisos de un rol.
   * Requiere permiso: ASSIGN_ROLE_PERMISSIONS
   */
  @Put(':id/permissions')
  @UseGuards(JwtAuthGuard, PermissionsGuard)
  @Permissions(Permission.ASSIGN_ROLE_PERMISSIONS)
  updateRolePermissions(
    @Param('id', ParseIntPipe) id: number,
    @Body() updateRolePermissionsDto: UpdateRolePermissionsDto,
  ) {
    return this.rolesService.updateRolePermissions(id, updateRolePermissionsDto);
  }

  @Patch(':id')
  update(
    @Param('id', ParseIntPipe) id: number,
    @Body() updateRoleDto: UpdateRoleDto,
  ) {
    return this.rolesService.update(id, updateRoleDto);
  }

  @Delete(':id')
  remove(@Param('id', ParseIntPipe) id: number) {
    return this.rolesService.remove(id);
  }
}
