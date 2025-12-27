import {
  Injectable,
  NotFoundException,
  ConflictException,
  Inject,
} from '@nestjs/common';
import { AreaModel } from './entities/area.entity';
import { CreateAreaDto } from './dto/create-area.dto';
import { UpdateAreaDto } from './dto/update-area.dto';
import { EmployeeModel } from '../employees/entities/employee.entity';
import { ServiceModel } from '../services/entities/service.entity';
import { type ModelClass } from 'objection';

@Injectable()
export class AreasService {
  constructor(
    @Inject(AreaModel.name) private areaModel: ModelClass<AreaModel>,
    @Inject(EmployeeModel.name)
    private employeeModel: ModelClass<EmployeeModel>,
    @Inject(ServiceModel.name) private serviceModel: ModelClass<ServiceModel>,
  ) {}

  async create(createAreaDto: CreateAreaDto) {
    // Verificar si ya existe un área con el mismo nombre
    const existing = await this.areaModel
      .query()
      .where('name', 'ilike', createAreaDto.name)
      .first();

    if (existing) {
      throw new ConflictException('Ya existe un área con ese nombre');
    }

    const area = await this.areaModel.query().insert({
      name: createAreaDto.name,
      description: createAreaDto.description,
    });

    return area;
  }

  async findAll() {
    return await this.areaModel.query().orderBy('name', 'asc');
  }

  async findOne(id: number) {
    const area = await this.areaModel.query().findById(id);

    if (!area) {
      throw new NotFoundException('Área no encontrada');
    }

    return area;
  }

  async update(id: number, updateAreaDto: UpdateAreaDto) {
    const area = await this.areaModel.query().findById(id);

    if (!area) {
      throw new NotFoundException('Área no encontrada');
    }

    // Verificar si el nuevo nombre ya existe en otra área
    if (updateAreaDto.name) {
      const existing = await this.areaModel
        .query()
        .where('name', 'ilike', updateAreaDto.name)
        .whereNot('id', id)
        .first();

      if (existing) {
        throw new ConflictException('Ya existe un área con ese nombre');
      }
    }

    const updated = await this.areaModel
      .query()
      .patchAndFetchById(id, updateAreaDto);

    return updated;
  }

  async remove(id: number) {
    const area = await this.areaModel.query().findById(id);

    if (!area) {
      throw new NotFoundException('Área no encontrada');
    }

    // Verificar si hay empleados asociados a esta área
    const employeesCount = await this.employeeModel
      .query()
      .where('area_id', id)
      .resultSize();

    if (employeesCount > 0) {
      throw new ConflictException(
        `No se puede eliminar el área porque tiene ${employeesCount} empleado(s) asociado(s)`,
      );
    }

    // Verificar si hay servicios asociados a esta área
    const servicesCount = await this.serviceModel
      .query()
      .where('area_id', id)
      .resultSize();

    if (servicesCount > 0) {
      throw new ConflictException(
        `No se puede eliminar el área porque tiene ${servicesCount} servicio(s) asociado(s)`,
      );
    }

    await this.areaModel.query().deleteById(id);

    return { message: 'Área eliminada exitosamente' };
  }
}
