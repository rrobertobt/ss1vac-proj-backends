import {
  Inject,
  Injectable,
  NotFoundException,
  BadRequestException,
} from '@nestjs/common';
import { CreateRoleDto } from './dto/create-role.dto';
import { UpdateRoleDto } from './dto/update-role.dto';
import { UpdateRolePermissionsDto } from './dto/update-role-permissions.dto';
import { RoleModel } from './entities/role.entity';
import { PermissionModel } from '../permissions/entities/permission.entity';
import { type ModelClass } from 'objection';

@Injectable()
export class RolesService {
  constructor(
    @Inject(RoleModel.name) private roleModel: ModelClass<RoleModel>,
    @Inject(PermissionModel.name)
    private permissionModel: ModelClass<PermissionModel>,
  ) {}

  create(createRoleDto: CreateRoleDto) {
    return 'This action adds a new role';
  }

  async findAll() {
    const roles = await this.roleModel
      .query()
      .select('id', 'name', 'label', 'description')
      .orderBy('name', 'asc');
    return roles;
  }

  async findOne(id: number) {
    const role = await this.roleModel
      .query()
      .findById(id)
      .select('id', 'name', 'label', 'description');

    if (!role) {
      throw new NotFoundException(`Rol con ID ${id} no encontrado`);
    }

    return role;
  }

  async getRolePermissions(roleId: number) {
    const role = await this.roleModel
      .query()
      .findById(roleId)
      .withGraphFetched('permissions')
      .select('id', 'name', 'label', 'description');

    if (!role) {
      throw new NotFoundException(`Rol con ID ${roleId} no encontrado`);
    }

    return {
      role: {
        id: role.id,
        name: role.name,
        label: role.label,
        description: role.description,
      },
      permissions: role.permissions || [],
    };
  }

  async updateRolePermissions(
    roleId: number,
    updateRolePermissionsDto: UpdateRolePermissionsDto,
  ) {
    const role = await this.roleModel.query().findById(roleId);

    if (!role) {
      throw new NotFoundException(`Rol con ID ${roleId} no encontrado`);
    }

    // Verificar que todos los permisos existen
    const permissions = await this.permissionModel
      .query()
      .whereIn('id', updateRolePermissionsDto.permission_ids);

    if (permissions.length !== updateRolePermissionsDto.permission_ids.length) {
      throw new BadRequestException(
        'Uno o más IDs de permisos no son válidos',
      );
    }

    // Usar transacción para asegurar consistencia
    const trx = await this.roleModel.startTransaction();

    try {
      // Eliminar todas las relaciones existentes
      await this.roleModel
        .relatedQuery('permissions', trx)
        .for(roleId)
        .unrelate();

      // Relacionar los nuevos permisos
      if (updateRolePermissionsDto.permission_ids.length > 0) {
        await this.roleModel
          .relatedQuery('permissions', trx)
          .for(roleId)
          .relate(updateRolePermissionsDto.permission_ids);
      }

      await trx.commit();

      // Retornar rol con sus nuevos permisos
      return this.getRolePermissions(roleId);
    } catch (error) {
      await trx.rollback();
      throw error;
    }
  }

  update(id: number, updateRoleDto: UpdateRoleDto) {
    return `This action updates a #${id} role`;
  }

  remove(id: number) {
    return `This action removes a #${id} role`;
  }
}
