import {
  Inject,
  Injectable,
  NotFoundException,
  BadRequestException,
} from '@nestjs/common';
import { CreatePatientTaskDto } from './dto/create-patient-task.dto';
import { UpdatePatientTaskDto } from './dto/update-patient-task.dto';
import { PatientTaskModel } from './entities/patient-task.entity';
import { PatientModel } from '../patients/entities/patient.entity';
import { ClinicalRecordModel } from '../clinical-records/entities/clinical-record.entity';
import { type ModelClass } from 'objection';

@Injectable()
export class PatientTasksService {
  constructor(
    @Inject(PatientTaskModel.name)
    private patientTaskModel: ModelClass<PatientTaskModel>,
    @Inject(PatientModel.name) private patientModel: ModelClass<PatientModel>,
    @Inject(ClinicalRecordModel.name)
    private clinicalRecordModel: ModelClass<ClinicalRecordModel>,
  ) {}

  async create(
    patientId: number,
    createDto: CreatePatientTaskDto,
    currentUser?: any,
  ): Promise<PatientTaskModel> {
    const trx = await this.patientTaskModel.startTransaction();

    try {
      // Verificar que el paciente existe
      const patient = await this.patientModel.query(trx).findById(patientId);

      if (!patient) {
        throw new NotFoundException(
          `Paciente con ID ${patientId} no encontrado`,
        );
      }

      // Verificar que el paciente esté activo
      if (patient.status !== 'ACTIVE') {
        throw new BadRequestException(
          'No se puede asignar tarea a un paciente inactivo',
        );
      }

      // Verificar historia clínica si se proporciona
      if (createDto.clinical_record_id) {
        const clinicalRecord = await this.clinicalRecordModel
          .query(trx)
          .findById(createDto.clinical_record_id);

        if (!clinicalRecord) {
          throw new NotFoundException(
            `Historia clínica con ID ${createDto.clinical_record_id} no encontrada`,
          );
        }

        // Verificar que la historia clínica pertenece al paciente
        if (clinicalRecord.patient_id !== patientId) {
          throw new BadRequestException(
            'La historia clínica no pertenece al paciente',
          );
        }
      }

      // Obtener employee_id del usuario actual (si está disponible)
      const assignedByEmployeeId = currentUser?.employee?.id || null;

      // Crear la tarea
      const task = await this.patientTaskModel.query(trx).insert({
        patient_id: patientId,
        clinical_record_id: createDto.clinical_record_id,
        assigned_by_employee_id: assignedByEmployeeId,
        title: createDto.title,
        description: createDto.description,
        due_date: createDto.due_date ? new Date(createDto.due_date) : null,
        status: 'PENDING',
      });

      await trx.commit();

      // Retornar con relaciones
      const createdTask = await this.patientTaskModel
        .query()
        .findById(task.id)
        .withGraphFetched('[patient, clinical_record, assigned_by]');

      return createdTask!;
    } catch (error) {
      await trx.rollback();
      throw error;
    }
  }

  async update(
    taskId: number,
    updateDto: UpdatePatientTaskDto,
  ): Promise<PatientTaskModel> {
    const trx = await this.patientTaskModel.startTransaction();

    try {
      const task = await this.patientTaskModel.query(trx).findById(taskId);

      if (!task) {
        throw new NotFoundException(`Tarea con ID ${taskId} no encontrada`);
      }

      // Actualizar solo los campos proporcionados
      const updateData: Partial<PatientTaskModel> = { ...updateDto } as any;
      if (updateDto.due_date) {
        (updateData as any).due_date = new Date(updateDto.due_date);
      }

      await this.patientTaskModel
        .query(trx)
        .patchAndFetchById(taskId, updateData);

      await trx.commit();

      // Retornar con relaciones
      const updatedTask = await this.patientTaskModel
        .query()
        .findById(taskId)
        .withGraphFetched('[patient, clinical_record, assigned_by]');

      return updatedTask!;
    } catch (error) {
      await trx.rollback();
      throw error;
    }
  }

  async findByPatient(patientId: number): Promise<PatientTaskModel[]> {
    return await this.patientTaskModel
      .query()
      .where('patient_id', patientId)
      .withGraphFetched('[clinical_record, assigned_by]')
      .orderBy('created_at', 'desc');
  }

  async findByCurrentPatient(currentUser: any): Promise<PatientTaskModel[]> {
    // Obtener el patient_id del usuario actual
    const patientId = currentUser?.patient?.id;

    if (!patientId) {
      throw new BadRequestException(
        'El usuario actual no tiene un paciente asociado',
      );
    }

    return await this.patientTaskModel
      .query()
      .where('patient_id', patientId)
      .withGraphFetched('[clinical_record, assigned_by]')
      .orderBy('created_at', 'desc');
  }
}
