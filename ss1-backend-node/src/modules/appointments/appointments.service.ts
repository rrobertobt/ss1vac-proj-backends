import { Injectable, NotFoundException } from '@nestjs/common';
import { AppointmentModel } from './entities/appointment.entity';
import { EmployeeAvailabilityModel } from './entities/employee-availability.entity';
import { CreateAppointmentDto } from './dto/create-appointment.dto';
import { UpdateAppointmentDto } from './dto/update-appointment.dto';
import { FilterAppointmentsDto } from './dto/filter-appointments.dto';
import { CheckAvailabilityDto } from './dto/check-availability.dto';

@Injectable()
export class AppointmentsService {
  /**
   * Consultar disponibilidad de citas
   * Calcula slots disponibles basados en:
   * - Disponibilidad del profesional (employee_availability)
   * - Citas ya agendadas
   * - Filtros opcionales: especialidad, área, profesional
   */
  async checkAvailability(dto: CheckAvailabilityDto) {
    const { date, specialtyId, professionalId } = dto;

    // Convertir fecha string a Date y obtener día de la semana (0=Domingo, 6=Sábado)
    const targetDate = new Date(date);
    const dayOfWeek = targetDate.getDay();

    // Query para obtener disponibilidades que coincidan con el día
    let availabilityQuery = EmployeeAvailabilityModel.query()
      .where('day_of_week', dayOfWeek)
      .where('is_active', true)
      .withGraphFetched('[employee, specialty]');

    // Filtrar por especialidad si se proporciona
    if (specialtyId) {
      availabilityQuery = availabilityQuery.where('specialty_id', specialtyId);
    }

    // Filtrar por profesional específico
    if (professionalId) {
      availabilityQuery = availabilityQuery.where(
        'employee_id',
        professionalId,
      );
    }

    const availabilities = await availabilityQuery;

    // Para cada disponibilidad, calcular slots de 1 hora
    const allSlots: any[] = [];

    for (const avail of availabilities) {
      // Obtener citas ya agendadas para este profesional en esta fecha
      const startOfDay = new Date(date);
      startOfDay.setHours(0, 0, 0, 0);
      const endOfDay = new Date(date);
      endOfDay.setHours(23, 59, 59, 999);

      const existingAppointments = await AppointmentModel.query()
        .where('professional_id', avail.employee_id)
        .where('start_datetime', '>=', startOfDay.toISOString())
        .where('start_datetime', '<', endOfDay.toISOString())
        .whereIn('status', ['SCHEDULED', 'COMPLETED']);

      // Generar slots de 1 hora dentro del horario disponible
      const slots = this.generateTimeSlots(
        avail.start_time,
        avail.end_time,
        existingAppointments,
        date,
      );

      allSlots.push({
        employee_id: avail.employee_id,
        employee_name: avail.employee
          ? `${avail.employee.first_name} ${avail.employee.last_name}`
          : 'N/A',
        specialty_id: avail.specialty_id,
        specialty_name: avail.specialty?.name || null,
        available_slots: slots,
      });
    }

    return {
      date,
      day_of_week: dayOfWeek,
      professionals: allSlots,
    };
  }

  /**
   * Genera slots de tiempo de 1 hora
   */

  private generateTimeSlots(
    startTime: string,
    endTime: string,
    existingAppointments: AppointmentModel[],
    date: string,
  ): any[] {
    const slots: any[] = [];
    const [startHour, startMin] = startTime.split(':').map(Number);
    const [endHour, endMin] = endTime.split(':').map(Number);

    let currentHour = startHour;
    const currentMin = startMin;

    while (
      currentHour < endHour ||
      (currentHour === endHour && currentMin < endMin)
    ) {
      const slotStart = new Date(date);
      slotStart.setHours(currentHour, currentMin, 0, 0);

      const slotEnd = new Date(slotStart);
      slotEnd.setHours(slotEnd.getHours() + 1); // Slots de 1 hora

      // Verificar si este slot NO tiene conflicto con citas existentes
      const hasConflict = existingAppointments.some((appt) => {
        const apptStart = new Date(appt.start_datetime);
        const apptEnd = new Date(appt.end_datetime);
        return slotStart < apptEnd && slotEnd > apptStart;
      });

      if (!hasConflict && slotEnd <= this.parseTime(endTime, date)) {
        slots.push({
          start: slotStart.toISOString(),
          end: slotEnd.toISOString(),
          available: true,
        });
      }

      // Avanzar 1 hora
      currentHour += 1;
      if (currentHour >= 24) break;
    }

    return slots;
  }

  private parseTime(timeStr: string, date: string): Date {
    const [hour, min] = timeStr.split(':').map(Number);
    const result = new Date(date);
    result.setHours(hour, min, 0, 0);
    return result;
  }

  /**
   * Crear una nueva cita
   */
  async create(dto: CreateAppointmentDto) {
    // Validar que end_datetime > start_datetime
    const start = new Date(dto.start_datetime);
    const end = new Date(dto.end_datetime);

    if (end <= start) {
      throw new Error('end_datetime debe ser posterior a start_datetime');
    }

    // Verificar que el profesional no tenga otra cita en ese horario
    if (dto.professional_id) {
      const conflicts = await AppointmentModel.query()
        .where('professional_id', dto.professional_id)
        .where('start_datetime', '<', dto.end_datetime)
        .where('end_datetime', '>', dto.start_datetime)
        .whereIn('status', ['SCHEDULED', 'COMPLETED']);

      if (conflicts.length > 0) {
        throw new Error(
          'El profesional ya tiene una cita agendada en ese horario',
        );
      }
    }

    // eslint-disable-next-line @typescript-eslint/no-unsafe-argument
    const appointment = await AppointmentModel.query().insertAndFetch({
      patient_id: dto.patient_id,
      professional_id: dto.professional_id || null,
      specialty_id: dto.specialty_id || null,
      appointment_type: dto.appointment_type || null,
      start_datetime: new Date(dto.start_datetime),
      end_datetime: new Date(dto.end_datetime),
      status: 'SCHEDULED',
      notes: dto.notes || null,
    } as any);

    return AppointmentModel.query()
      .findById(appointment.id)
      .withGraphFetched('[patient, professional, specialty]');
  }

  /**
   * Listar citas con filtros
   */
  async findAll(dto: FilterAppointmentsDto) {
    const {
      from,
      to,
      professionalId,
      patientId,
      status,
      page = 1,
      limit = 20,
    } = dto;

    let query = AppointmentModel.query().withGraphFetched(
      '[patient, professional, specialty]',
    );

    // Filtro de fechas
    if (from) {
      const startDate = new Date(from);
      startDate.setHours(0, 0, 0, 0);
      query = query.where('start_datetime', '>=', startDate.toISOString());
    }

    if (to) {
      const endDate = new Date(to);
      endDate.setHours(23, 59, 59, 999);
      query = query.where('start_datetime', '<=', endDate.toISOString());
    }

    // Filtro por profesional
    if (professionalId) {
      query = query.where('professional_id', professionalId);
    }

    // Filtro por paciente
    if (patientId) {
      query = query.where('patient_id', patientId);
    }

    // Filtro por estado
    if (status) {
      query = query.where('status', status);
    }

    // Orden descendente por fecha
    query = query.orderBy('start_datetime', 'desc');

    // Paginación
    const offset = (page - 1) * limit;
    const [appointments, total] = await Promise.all([
      query.clone().limit(limit).offset(offset),
      query.clone().resultSize(),
    ]);

    return {
      data: appointments,
      meta: {
        total,
        page,
        limit,
        totalPages: Math.ceil(total / limit),
      },
    };
  }

  /**
   * Obtener citas del paciente actual (para portal de paciente)
   */
  async findMyAppointments(patientId: number) {
    const appointments = await AppointmentModel.query()
      .where('patient_id', patientId)
      .withGraphFetched('[professional, specialty]')
      .orderBy('start_datetime', 'desc');

    return appointments;
  }

  /**
   * Obtener citas del profesional actual (para psicólogos/psiquiatras)
   */
  async findMyProfessionalAppointments(professionalId: number) {
    const appointments = await AppointmentModel.query()
      .where('professional_id', professionalId)
      .withGraphFetched('[patient, specialty]')
      .orderBy('start_datetime', 'desc');

    return appointments;
  }

  /**
   * Obtener detalle de una cita
   */
  async findOne(id: number) {
    const appointment = await AppointmentModel.query()
      .findById(id)
      .withGraphFetched('[patient, professional, specialty]');

    if (!appointment) {
      throw new NotFoundException(`Cita con ID ${id} no encontrada`);
    }

    return appointment;
  }

  /**
   * Actualizar/reprogramar una cita
   */
  async update(id: number, dto: UpdateAppointmentDto) {
    const appointment = await this.findOne(id);

    // Si se cambian las fechas, validar
    if (dto.start_datetime || dto.end_datetime) {
      const newStart = dto.start_datetime
        ? new Date(dto.start_datetime)
        : new Date(appointment.start_datetime);
      const newEnd = dto.end_datetime
        ? new Date(dto.end_datetime)
        : new Date(appointment.end_datetime);

      if (newEnd <= newStart) {
        throw new Error('end_datetime debe ser posterior a start_datetime');
      }

      // Verificar conflictos si cambia profesional o horarios
      const professionalId = dto.professional_id ?? appointment.professional_id;

      if (professionalId) {
        const conflicts = await AppointmentModel.query()
          .where('professional_id', professionalId)
          .where('id', '!=', id)
          .where('start_datetime', '<', newEnd.toISOString())
          .where('end_datetime', '>', newStart.toISOString())
          .whereIn('status', ['SCHEDULED', 'COMPLETED']);

        if (conflicts.length > 0) {
          throw new Error(
            'El profesional ya tiene una cita agendada en ese horario',
          );
        }
      }
    }

    const updateData: any = {};
    if (dto.professional_id !== undefined)
      // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
      updateData.professional_id = dto.professional_id;

    if (dto.specialty_id !== undefined)
      updateData.specialty_id = dto.specialty_id;
    if (dto.appointment_type !== undefined)
      // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
      updateData.appointment_type = dto.appointment_type;
    if (dto.start_datetime !== undefined)
      // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
      updateData.start_datetime = new Date(dto.start_datetime);
    if (dto.end_datetime !== undefined)
      // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
      updateData.end_datetime = new Date(dto.end_datetime);
    // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
    if (dto.notes !== undefined) updateData.notes = dto.notes;
    // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
    updateData.updated_at = new Date();

    const updated = await AppointmentModel.query().patchAndFetchById(
      id,
      updateData,
    );

    return AppointmentModel.query()
      .findById(updated.id)
      .withGraphFetched('[patient, professional, specialty]');
  }

  /**
   * Cancelar una cita
   */
  async cancel(id: number) {
    const appointment = await this.findOne(id);

    if (appointment.status === 'CANCELLED') {
      throw new Error('La cita ya está cancelada');
    }

    if (appointment.status === 'COMPLETED') {
      throw new Error('No se puede cancelar una cita completada');
    }

    await AppointmentModel.query().patchAndFetchById(id, {
      status: 'CANCELLED',
      updated_at: new Date(),
    });

    return this.findOne(id);
  }

  /**
   * Marcar cita como atendida/completada
   */
  async complete(id: number) {
    const appointment = await this.findOne(id);

    if (appointment.status === 'CANCELLED') {
      throw new Error('No se puede completar una cita cancelada');
    }

    if (appointment.status === 'COMPLETED') {
      throw new Error('La cita ya está marcada como completada');
    }

    await AppointmentModel.query().patchAndFetchById(id, {
      status: 'COMPLETED',
      updated_at: new Date(),
    });

    return this.findOne(id);
  }
}
