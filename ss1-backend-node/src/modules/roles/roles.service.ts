import { Inject, Injectable } from '@nestjs/common';
import { CreateRoleDto } from './dto/create-role.dto';
import { UpdateRoleDto } from './dto/update-role.dto';
import { RoleModel } from './entities/role.entity';
import { type ModelClass } from 'objection';

@Injectable()
export class RolesService {
  constructor(
    @Inject(RoleModel.name) private roleModel: ModelClass<RoleModel>,
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

  findOne(id: number) {
    return `This action returns a #${id} role`;
  }

  update(id: number, updateRoleDto: UpdateRoleDto) {
    return `This action updates a #${id} role`;
  }

  remove(id: number) {
    return `This action removes a #${id} role`;
  }
}
