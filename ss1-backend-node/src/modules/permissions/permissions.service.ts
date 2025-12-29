import { Inject, Injectable } from '@nestjs/common';
import { PermissionModel } from './entities/permission.entity';
import { type ModelClass } from 'objection';

@Injectable()
export class PermissionsService {
  constructor(
    @Inject(PermissionModel.name)
    private permissionModel: ModelClass<PermissionModel>,
  ) {}

  async findAll() {
    const permissions = await this.permissionModel
      .query()
      .select('id', 'code', 'description')
      .orderBy('code', 'asc');
    return permissions;
  }
}
