import {
  Inject,
  Injectable,
  NotFoundException,
  BadRequestException,
} from '@nestjs/common';
import { CreateSessionDto } from './dto/create-session.dto';
import { UpdateSessionDto } from './dto/update-session.dto';
import { SessionModel } from './entities/session.entity';
import { ClinicalRecordModel } from '../clinical-records/entities/clinical-record.entity';
import { EmployeeModel } from '../employees/entities/employee.entity';
import { type ModelClass } from 'objection';

@Injectable()
export class SessionsService {
  constructor(
    @Inject(SessionModel.name) private sessionModel: ModelClass<SessionModel>,
    @Inject(ClinicalRecordModel.name)
    private clinicalRecordModel: ModelClass<ClinicalRecordModel>,
    @Inject(EmployeeModel.name)
    private employeeModel: ModelClass<EmployeeModel>,
  ) {}

  async create(
    clinicalRecordId: number,
    createDto: CreateSessionDto,
    currentUser?: any,
  ): Promise<SessionModel> {
    console.log(currentUser);
    const trx = await this.sessionModel.startTransaction();

    try {
      // Verificar que la historia clínica existe
      const clinicalRecord = await this.clinicalRecordModel
        .query(trx)
        .findById(clinicalRecordId);

      if (!clinicalRecord) {
        throw new NotFoundException(
          `Historia clínica con ID ${clinicalRecordId} no encontrada`,
        );
      }

      // Verificar que la historia clínica esté activa
      if (clinicalRecord.status !== 'ACTIVE') {
        throw new BadRequestException(
          'No se puede agregar sesión a una historia clínica cerrada',
        );
      }

      // Verificar profesional si se proporciona
      if (createDto.professional_id) {
        const professional = await this.employeeModel
          .query(trx)
          .findById(createDto.professional_id);

        if (!professional) {
          throw new NotFoundException(
            `Profesional con ID ${createDto.professional_id} no encontrado`,
          );
        }

        if (professional.status !== 'ACTIVE') {
          throw new BadRequestException(
            'No se puede asignar un profesional inactivo',
          );
        }
      }

      // Usar el professional_id del usuario actual si no se proporciona
      const professionalId =
        createDto.professional_id || currentUser?.employee.id || null;

      // Crear la sesión
      const session = await this.sessionModel.query(trx).insert({
        clinical_record_id: clinicalRecordId,
        professional_id: professionalId,
        session_datetime: new Date(createDto.session_datetime),
        session_number: createDto.session_number,
        attended: createDto.attended ?? true,
        absence_reason: createDto.absence_reason,
        topics: createDto.topics,
        interventions: createDto.interventions,
        patient_response: createDto.patient_response,
        assigned_tasks: createDto.assigned_tasks,
        observations: createDto.observations,
        next_appointment_datetime: createDto.next_appointment_datetime
          ? new Date(createDto.next_appointment_datetime)
          : null,
        appointment_id: createDto.appointment_id,
      });

      await trx.commit();

      // Retornar con relaciones
      const createdSession = await this.sessionModel
        .query()
        .findById(session.id)
        .withGraphFetched('[clinical_record, professional]');

      return createdSession!;
    } catch (error) {
      await trx.rollback();
      throw error;
    }
  }

  async update(
    sessionId: number,
    updateDto: UpdateSessionDto,
  ): Promise<SessionModel> {
    const trx = await this.sessionModel.startTransaction();

    try {
      const session = await this.sessionModel.query(trx).findById(sessionId);

      if (!session) {
        throw new NotFoundException(`Sesión con ID ${sessionId} no encontrada`);
      }

      // Verificar profesional si se cambia
      if (
        updateDto.professional_id &&
        updateDto.professional_id !== session.professional_id
      ) {
        const professional = await this.employeeModel
          .query(trx)
          .findById(updateDto.professional_id);

        if (!professional) {
          throw new NotFoundException(
            `Profesional con ID ${updateDto.professional_id} no encontrado`,
          );
        }

        if (professional.status !== 'ACTIVE') {
          throw new BadRequestException(
            'No se puede asignar un profesional inactivo',
          );
        }
      }

      // Actualizar solo los campos proporcionados
      const updateData: Partial<SessionModel> = { ...updateDto } as any;
      if (updateDto.session_datetime) {
        (updateData as any).session_datetime = new Date(
          updateDto.session_datetime,
        );
      }
      if (updateDto.next_appointment_datetime) {
        (updateData as any).next_appointment_datetime = new Date(
          updateDto.next_appointment_datetime,
        );
      }

      await this.sessionModel
        .query(trx)
        .patchAndFetchById(sessionId, updateData);

      await trx.commit();

      // Retornar con relaciones
      const updatedSession = await this.sessionModel
        .query()
        .findById(sessionId)
        .withGraphFetched('[clinical_record, professional]');

      return updatedSession!;
    } catch (error) {
      await trx.rollback();
      throw error;
    }
  }

  async findByClinicalRecord(
    clinicalRecordId: number,
  ): Promise<SessionModel[]> {
    // Verificar que la historia clínica existe
    const clinicalRecord = await this.clinicalRecordModel
      .query()
      .findById(clinicalRecordId);

    if (!clinicalRecord) {
      throw new NotFoundException(
        `Historia clínica con ID ${clinicalRecordId} no encontrada`,
      );
    }

    return await this.sessionModel
      .query()
      .where('clinical_record_id', clinicalRecordId)
      .withGraphFetched('[professional]')
      .orderBy('session_datetime', 'desc');
  }
}
