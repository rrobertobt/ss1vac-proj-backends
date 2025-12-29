import {
  Controller,
  Get,
  Post,
  Patch,
  Param,
  Query,
  Body,
  UseGuards,
  ParseIntPipe,
  Req,
} from '@nestjs/common';
import { AppointmentsService } from './appointments.service';
import { CreateAppointmentDto } from './dto/create-appointment.dto';
import { UpdateAppointmentDto } from './dto/update-appointment.dto';
import { FilterAppointmentsDto } from './dto/filter-appointments.dto';
import { CheckAvailabilityDto } from './dto/check-availability.dto';
import { JwtAuthGuard } from 'src/core/auth/guards/jwt-auth.guard';
import { PermissionsGuard } from 'src/core/auth/guards/permissions.guard';
import { Permissions } from 'src/core/decorators/permissions.decorator';
import { Permission } from 'src/core/enums/permissions.enum';

@Controller('appointments')
@UseGuards(JwtAuthGuard, PermissionsGuard)
export class AppointmentsController {
  constructor(private readonly appointmentsService: AppointmentsService) {}

  /**
   * A) Consultar disponibilidad
   * GET /appointments/availability?date=YYYY-MM-DD&specialtyId=&areaId=&professionalId=
   * Permiso: VIEW_SCHEDULED_APPOINTMENTS
   * Roles: ADMIN_STAFF, PSYCHOLOGIST, PSYCHIATRIST, SUPER_ADMIN
   */
  @Get('availability')
  @Permissions(Permission.VIEW_SCHEDULED_APPOINTMENTS)
  checkAvailability(@Query() dto: CheckAvailabilityDto) {
    return this.appointmentsService.checkAvailability(dto);
  }

  /**
   * G) Obtener citas del paciente actual
   * GET /appointments/my-appointments
   * Sin permisos específicos - el paciente solo ve sus propias citas
   * Roles: PATIENT
   */
  @Get('my-appointments')
  findMyAppointments(@Req() req: any) {
    // Obtener patient_id del usuario autenticado
    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-member-access
    const user = req.user;

    // Buscar el patient_id asociado a este user
    // Asumiendo que tienes una relación en el user
    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-member-access
    const patientId = user.patient_id; // O como tengas estructurado tu modelo

    if (!patientId) {
      throw new Error('Usuario no está asociado a un paciente');
    }

    // eslint-disable-next-line @typescript-eslint/no-unsafe-argument
    return this.appointmentsService.findMyAppointments(patientId);
  }

  /**
   * H) Obtener citas del profesional actual
   * GET /appointments/my-professional-appointments
   * Sin permisos específicos - el profesional solo ve sus propias citas asignadas
   * Roles: PSYCHOLOGIST, PSYCHIATRIST
   */
  @Get('my-professional-appointments')
  findMyProfessionalAppointments(@Req() req: any) {
    // Obtener employee_id del usuario autenticado
    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-member-access
    const user = req.user;

    // Buscar el employee_id asociado a este user
    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-member-access
    const employeeId = user.employee_id; // O como tengas estructurado tu modelo

    if (!employeeId) {
      throw new Error('Usuario no está asociado a un empleado');
    }

    // eslint-disable-next-line @typescript-eslint/no-unsafe-argument
    return this.appointmentsService.findMyProfessionalAppointments(employeeId);
  }

  /**
   * B) Crear cita
   * POST /appointments
   * Permiso: CREATE_APPOINTMENTS
   * Roles: ADMIN_STAFF, SUPER_ADMIN
   */
  @Post()
  @Permissions(Permission.CREATE_APPOINTMENTS)
  create(@Body() dto: CreateAppointmentDto) {
    return this.appointmentsService.create(dto);
  }

  /**
   * C) Listar citas
   * GET /appointments?from=&to=&professionalId=&patientId=&status=
   * Permiso: VIEW_SCHEDULED_APPOINTMENTS
   * Roles: ADMIN_STAFF, PSYCHOLOGIST, PSYCHIATRIST, SUPER_ADMIN
   *
   * Nota: Si quieres que los profesionales solo vean sus propias citas,
   * implementa lógica adicional en el servicio basado en el rol
   */
  @Get()
  @Permissions(Permission.VIEW_SCHEDULED_APPOINTMENTS)
  findAll(@Query() dto: FilterAppointmentsDto) {
    return this.appointmentsService.findAll(dto);
  }

  /**
   * Obtener detalle de una cita específica
   * GET /appointments/:id
   * Permiso: VIEW_SCHEDULED_APPOINTMENTS
   */
  @Get(':id')
  @Permissions(Permission.VIEW_SCHEDULED_APPOINTMENTS)
  findOne(@Param('id', ParseIntPipe) id: number) {
    return this.appointmentsService.findOne(id);
  }

  /**
   * D) Reprogramar/editar cita
   * PATCH /appointments/:id
   * Permiso: EDIT_APPOINTMENTS
   * Roles: ADMIN_STAFF, SUPER_ADMIN
   */
  @Patch(':id')
  @Permissions(Permission.EDIT_APPOINTMENTS)
  update(
    @Param('id', ParseIntPipe) id: number,
    @Body() dto: UpdateAppointmentDto,
  ) {
    return this.appointmentsService.update(id, dto);
  }

  /**
   * E) Cancelar cita
   * POST /appointments/:id/cancel
   * Permiso: CANCEL_APPOINTMENTS
   * Roles: ADMIN_STAFF, SUPER_ADMIN
   */
  @Post(':id/cancel')
  @Permissions(Permission.CANCEL_APPOINTMENTS)
  cancel(@Param('id', ParseIntPipe) id: number) {
    return this.appointmentsService.cancel(id);
  }

  /**
   * F) Marcar como atendida/completada
   * POST /appointments/:id/complete
   * Permiso: EDIT_APPOINTMENTS
   * Roles: PSYCHOLOGIST, PSYCHIATRIST, SUPER_ADMIN
   */
  @Post(':id/complete')
  @Permissions(Permission.EDIT_APPOINTMENTS)
  complete(@Param('id', ParseIntPipe) id: number) {
    return this.appointmentsService.complete(id);
  }
}
