import {
  Injectable,
  NotFoundException,
  ConflictException,
  Inject,
} from '@nestjs/common';
import { SpecialtyModel } from './entities/specialty.entity';
import { CreateSpecialtyDto } from './dto/create-specialty.dto';
import { UpdateSpecialtyDto } from './dto/update-specialty.dto';
import { EmployeeSpecialtyModel } from './entities/employee-specialty.entity';
import { type ModelClass } from 'objection';

@Injectable()
export class SpecialtiesService {
  constructor(
    @Inject(SpecialtyModel.name)
    private specialtyModel: ModelClass<SpecialtyModel>,
    @Inject(EmployeeSpecialtyModel.name)
    private employeeSpecialtyModel: ModelClass<EmployeeSpecialtyModel>,
  ) {}

  async create(createSpecialtyDto: CreateSpecialtyDto) {
    // Verificar si ya existe una especialidad con el mismo nombre
    const existing = await this.specialtyModel
      .query()
      .where('name', 'ilike', createSpecialtyDto.name)
      .first();

    if (existing) {
      throw new ConflictException('Ya existe una especialidad con ese nombre');
    }

    const specialty = await this.specialtyModel.query().insert({
      name: createSpecialtyDto.name,
      description: createSpecialtyDto.description,
    });

    return specialty;
  }

  async findAll() {
    return await this.specialtyModel.query().orderBy('name', 'asc');
  }

  async findOne(id: number) {
    const specialty = await this.specialtyModel.query().findById(id);

    if (!specialty) {
      throw new NotFoundException('Especialidad no encontrada');
    }

    return specialty;
  }

  async update(id: number, updateSpecialtyDto: UpdateSpecialtyDto) {
    const specialty = await this.specialtyModel.query().findById(id);

    if (!specialty) {
      throw new NotFoundException('Especialidad no encontrada');
    }

    // Verificar si el nuevo nombre ya existe en otra especialidad
    if (updateSpecialtyDto.name) {
      const existing = await this.specialtyModel
        .query()
        .where('name', 'ilike', updateSpecialtyDto.name)
        .whereNot('id', id)
        .first();

      if (existing) {
        throw new ConflictException(
          'Ya existe una especialidad con ese nombre',
        );
      }
    }

    const updated = await this.specialtyModel
      .query()
      .patchAndFetchById(id, updateSpecialtyDto);

    return updated;
  }

  async remove(id: number) {
    const specialty = await this.specialtyModel.query().findById(id);

    if (!specialty) {
      throw new NotFoundException('Especialidad no encontrada');
    }

    // Verificar si hay empleados asociados a esta especialidad
    const employeesCount = await this.employeeSpecialtyModel
      .query()
      .where('specialty_id', id)
      .resultSize();

    if (employeesCount > 0) {
      throw new ConflictException(
        `No se puede eliminar la especialidad porque tiene ${employeesCount} empleado(s) asociado(s)`,
      );
    }

    await this.specialtyModel.query().deleteById(id);

    return { message: 'Especialidad eliminada exitosamente' };
  }
}
