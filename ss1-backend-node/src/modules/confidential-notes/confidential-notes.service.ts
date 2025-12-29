import {
  Inject,
  Injectable,
  NotFoundException,
  BadRequestException,
} from '@nestjs/common';
import { CreateConfidentialNoteDto } from './dto/create-confidential-note.dto';
import { ConfidentialNoteModel } from './entities/confidential-note.entity';
import { ClinicalRecordModel } from '../clinical-records/entities/clinical-record.entity';
import { type ModelClass } from 'objection';

@Injectable()
export class ConfidentialNotesService {
  constructor(
    @Inject(ConfidentialNoteModel.name)
    private confidentialNoteModel: ModelClass<ConfidentialNoteModel>,
    @Inject(ClinicalRecordModel.name)
    private clinicalRecordModel: ModelClass<ClinicalRecordModel>,
  ) {}

  async create(
    clinicalRecordId: number,
    createDto: CreateConfidentialNoteDto,
    currentUser?: any,
  ): Promise<ConfidentialNoteModel> {
    const trx = await this.confidentialNoteModel.startTransaction();

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
          'No se puede agregar nota a una historia clínica cerrada',
        );
      }

      // Obtener employee_id del usuario actual (si está disponible)
      const authorEmployeeId = currentUser?.employee_id || null;

      // Crear la nota confidencial
      const note = await this.confidentialNoteModel.query(trx).insert({
        patient_id: clinicalRecord.patient_id,
        clinical_record_id: clinicalRecordId,
        author_employee_id: authorEmployeeId,
        content: createDto.content,
      });

      await trx.commit();

      // Retornar con relaciones
      const createdNote = await this.confidentialNoteModel
        .query()
        .findById(note.id)
        .withGraphFetched('[author]');

      return createdNote!;
    } catch (error) {
      await trx.rollback();
      throw error;
    }
  }

  async findByClinicalRecord(
    clinicalRecordId: number,
  ): Promise<ConfidentialNoteModel[]> {
    // Verificar que la historia clínica existe
    const clinicalRecord = await this.clinicalRecordModel
      .query()
      .findById(clinicalRecordId);

    if (!clinicalRecord) {
      throw new NotFoundException(
        `Historia clínica con ID ${clinicalRecordId} no encontrada`,
      );
    }

    return await this.confidentialNoteModel
      .query()
      .where('clinical_record_id', clinicalRecordId)
      .withGraphFetched('[author]')
      .orderBy('created_at', 'desc');
  }
}
