import {
  Inject,
  Injectable,
  NotFoundException,
  BadRequestException,
  ConflictException,
} from '@nestjs/common';
import { CreateClinicalRecordDto } from './dto/create-clinical-record.dto';
import { UpdateClinicalRecordDto } from './dto/update-clinical-record.dto';
import { FilterClinicalRecordsDto } from './dto/filter-clinical-records.dto';
import { ClinicalRecordModel } from './entities/clinical-record.entity';
import { PatientModel } from '../patients/entities/patient.entity';
import { EmployeeModel } from '../employees/entities/employee.entity';
import { type ModelClass } from 'objection';

@Injectable()
export class ClinicalRecordsService {
  constructor(
    @Inject(ClinicalRecordModel.name)
    private clinicalRecordModel: ModelClass<ClinicalRecordModel>,
    @Inject(PatientModel.name) private patientModel: ModelClass<PatientModel>,
    @Inject(EmployeeModel.name)
    private employeeModel: ModelClass<EmployeeModel>,
  ) {}

  async create(
    createDto: CreateClinicalRecordDto,
    _currentUser?: any,
  ): Promise<ClinicalRecordModel> {
    const trx = await this.clinicalRecordModel.startTransaction();

    try {
      // Verificar que el paciente existe
      const patient = await this.patientModel
        .query(trx)
        .findById(createDto.patient_id);

      if (!patient) {
        throw new NotFoundException(
          `Paciente con ID ${createDto.patient_id} no encontrado`,
        );
      }

      // Verificar que el paciente esté activo
      if (patient.status !== 'ACTIVE') {
        throw new BadRequestException(
          'No se puede crear historia clínica para un paciente inactivo',
        );
      }

      // Verificar empleado responsable si se proporciona
      if (createDto.responsible_employee_id) {
        const employee = await this.employeeModel
          .query(trx)
          .findById(createDto.responsible_employee_id);

        if (!employee) {
          throw new NotFoundException(
            `Empleado con ID ${createDto.responsible_employee_id} no encontrado`,
          );
        }

        if (employee.status !== 'ACTIVE') {
          throw new BadRequestException(
            'No se puede asignar un empleado inactivo como responsable',
          );
        }
      }

      // Verificar si ya existe un número de historia clínica
      if (createDto.record_number) {
        const existingRecord = await this.clinicalRecordModel
          .query(trx)
          .where('record_number', createDto.record_number)
          .first();

        if (existingRecord) {
          throw new ConflictException(
            `Ya existe una historia clínica con el número ${createDto.record_number}`,
          );
        }
      }

      // Crear la historia clínica
      const clinicalRecord = await this.clinicalRecordModel.query(trx).insert({
        patient_id: createDto.patient_id,
        record_number: createDto.record_number,
        institution_name: createDto.institution_name,
        service: createDto.service,
        opening_date: createDto.opening_date
          ? new Date(createDto.opening_date)
          : new Date(),
        responsible_employee_id: createDto.responsible_employee_id,
        responsible_license: createDto.responsible_license,
        referral_source: createDto.referral_source,
        chief_complaint: createDto.chief_complaint,
        status: 'ACTIVE',
      });

      await trx.commit();

      // Retornar con relaciones
      const record = await this.clinicalRecordModel
        .query()
        .findById(clinicalRecord.id)
        .withGraphFetched('[patient, responsible_employee]');

      return record!;
    } catch (error) {
      await trx.rollback();
      throw error;
    }
  }

  async findAll(
    filters: FilterClinicalRecordsDto,
    _currentUser?: any,
  ): Promise<{
    data: ClinicalRecordModel[];
    meta: {
      total: number;
      page: number;
      limit: number;
      totalPages: number;
    };
  }> {
    const { patientId, professionalId, status, page = 1, limit = 10 } = filters;

    let query = this.clinicalRecordModel
      .query()
      .withGraphFetched('[patient, responsible_employee]')
      .orderBy('created_at', 'desc');

    // Filtrar por paciente
    if (patientId) {
      query = query.where('patient_id', patientId);
    }

    // Filtrar por profesional responsable
    if (professionalId) {
      query = query.where('responsible_employee_id', professionalId);
    }

    // Filtrar por estado
    if (status) {
      query = query.where('status', status);
    }

    // TODO: Implementar lógica para que el profesional solo vea sus propias historias
    // if (currentUser && currentUser.role === 'PSYCHOLOGIST') {
    //   query = query.where('responsible_employee_id', currentUser.employee_id);
    // }

    // Paginación
    const offset = (page - 1) * limit;
    const total = await query.resultSize();
    const data = await query.offset(offset).limit(limit);

    return {
      data,
      meta: {
        total,
        page,
        limit,
        totalPages: Math.ceil(total / limit),
      },
    };
  }

  async findOne(id: number, _currentUser?: any): Promise<ClinicalRecordModel> {
    const clinicalRecord = await this.clinicalRecordModel
      .query()
      .findById(id)
      .withGraphFetched('[patient, responsible_employee]');

    if (!clinicalRecord) {
      throw new NotFoundException(
        `Historia clínica con ID ${id} no encontrada`,
      );
    }

    // TODO: Verificar permisos - profesional solo puede ver sus propias historias
    // if (currentUser && currentUser.role === 'PSYCHOLOGIST') {
    //   if (clinicalRecord.responsible_employee_id !== currentUser.employee_id) {
    //     throw new ForbiddenException('No tiene permiso para ver esta historia clínica');
    //   }
    // }

    return clinicalRecord;
  }

  async update(
    id: number,
    updateDto: UpdateClinicalRecordDto,
    _currentUser?: any,
  ): Promise<ClinicalRecordModel> {
    const trx = await this.clinicalRecordModel.startTransaction();

    try {
      const clinicalRecord = await this.clinicalRecordModel
        .query(trx)
        .findById(id);

      if (!clinicalRecord) {
        throw new NotFoundException(
          `Historia clínica con ID ${id} no encontrada`,
        );
      }

      // TODO: Verificar permisos - profesional solo puede editar sus propias historias
      // if (currentUser && currentUser.role === 'PSYCHOLOGIST') {
      //   if (clinicalRecord.responsible_employee_id !== currentUser.employee_id) {
      //     throw new ForbiddenException('No tiene permiso para editar esta historia clínica');
      //   }
      // }

      // Verificar empleado responsable si se cambia
      if (
        updateDto.responsible_employee_id &&
        updateDto.responsible_employee_id !==
          clinicalRecord.responsible_employee_id
      ) {
        const employee = await this.employeeModel
          .query(trx)
          .findById(updateDto.responsible_employee_id);

        if (!employee) {
          throw new NotFoundException(
            `Empleado con ID ${updateDto.responsible_employee_id} no encontrado`,
          );
        }

        if (employee.status !== 'ACTIVE') {
          throw new BadRequestException(
            'No se puede asignar un empleado inactivo como responsable',
          );
        }
      }

      // Verificar número de historia clínica si se cambia
      if (
        updateDto.record_number &&
        updateDto.record_number !== clinicalRecord.record_number
      ) {
        const existingRecord = await this.clinicalRecordModel
          .query(trx)
          .where('record_number', updateDto.record_number)
          .whereNot('id', id)
          .first();

        if (existingRecord) {
          throw new ConflictException(
            `Ya existe una historia clínica con el número ${updateDto.record_number}`,
          );
        }
      }

      // Actualizar
      const updateData: Partial<ClinicalRecordModel> = { ...updateDto } as any;
      if (updateDto.opening_date) {
        (updateData as any).opening_date = new Date(updateDto.opening_date);
      }

      await this.clinicalRecordModel
        .query(trx)
        .patchAndFetchById(id, updateData);

      await trx.commit();

      // Retornar con relaciones
      const updatedRecord = await this.clinicalRecordModel
        .query()
        .findById(id)
        .withGraphFetched('[patient, responsible_employee]');

      return updatedRecord!;
    } catch (error) {
      await trx.rollback();
      throw error;
    }
  }

  async findByCurrentPatient(currentUser: any): Promise<ClinicalRecordModel[]> {
    // Obtener el patient_id del usuario actual
    const patientId = currentUser?.patient?.id;

    if (!patientId) {
      throw new BadRequestException(
        'El usuario actual no tiene un paciente asociado',
      );
    }

    return await this.clinicalRecordModel
      .query()
      .where('patient_id', patientId)
      .withGraphFetched('[responsible_employee]')
      .orderBy('created_at', 'desc');
  }
}
