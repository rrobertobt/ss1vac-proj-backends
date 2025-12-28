import { ConflictException, Inject, Injectable } from '@nestjs/common';
import * as bcrypt from 'bcrypt';
import * as crypto from 'crypto';
import { type ModelClass } from 'objection';
import { MailService } from '../mail/mailtrap.service';
import { UserModel } from '../users/entities/user.entity';
import { CreateEmployeeDto } from './dto/create-employee.dto';
import { EmployeeModel } from './entities/employee.entity';
import { EmployeeAvailabilityModel } from './entities/employee-availability.entity';

@Injectable()
export class EmployeesService {
  constructor(
    @Inject(EmployeeModel.name)
    private employeeModel: ModelClass<EmployeeModel>,
    @Inject(UserModel.name) private userModel: ModelClass<UserModel>,
    @Inject(EmployeeAvailabilityModel.name)
    private employeeAvailabilityModel: ModelClass<EmployeeAvailabilityModel>,
    private readonly mailService: MailService,
  ) {}

  async create(createEmployeeDto: CreateEmployeeDto) {
    // Verificar si el email ya existe
    const existingUser = await this.userModel
      .query()
      .where('email', createEmployeeDto.email)
      .first();

    if (existingUser) {
      throw new ConflictException('El email ya está registrado');
    }

    // Verificar si el username ya existe (si se proporcionó)
    if (createEmployeeDto.username) {
      const existingUsername = await this.userModel
        .query()
        .where('username', createEmployeeDto.username)
        .first();

      if (existingUsername) {
        throw new ConflictException('El username ya está registrado');
      }
    }

    // Generar contraseña aleatoria
    const generatedPassword = this.generatePassword();
    const hashedPassword = await bcrypt.hash(generatedPassword, 10);

    // Iniciar transacción
    const trx = await this.userModel.startTransaction();

    try {
      // Crear usuario
      const user = await this.userModel.query(trx).insert({
        email: createEmployeeDto.email,
        username: createEmployeeDto.username,
        password_hash: hashedPassword,
        role_id: createEmployeeDto.role_id,
        is_active: true,
      });

      // Crear empleado
      const employee = await this.employeeModel.query(trx).insert({
        user_id: user.id,
        first_name: createEmployeeDto.first_name,
        last_name: createEmployeeDto.last_name,
        employee_type: createEmployeeDto.employee_type,
        license_number: createEmployeeDto.license_number,
        area_id: createEmployeeDto.area_id,
        base_salary: createEmployeeDto.base_salary ?? 0,
        session_rate: createEmployeeDto.session_rate ?? 0,
        igss_percentage: createEmployeeDto.igss_percentage ?? 0,
        hired_at: createEmployeeDto.hired_at
          ? new Date(createEmployeeDto.hired_at)
          : null,
        status: 'ACTIVE',
      });

      // Asignar especialidades si se proporcionaron
      if (
        createEmployeeDto.specialty_ids &&
        createEmployeeDto.specialty_ids.length > 0
      ) {
        const specialtyRecords = createEmployeeDto.specialty_ids.map(
          (specialtyId) => ({
            employee_id: employee.id,
            specialty_id: specialtyId,
          }),
        );

        await this.employeeAvailabilityModel
          .knex()
          .raw(
            'INSERT INTO employee_specialties (employee_id, specialty_id) VALUES ' +
              specialtyRecords.map(() => '(?, ?)').join(', '),
            specialtyRecords.flatMap((r) => [r.employee_id, r.specialty_id]),
          )
          .transacting(trx);
      }

      // Crear registros de disponibilidad si se proporcionaron
      if (
        createEmployeeDto.availability &&
        createEmployeeDto.availability.length > 0
      ) {
        const assignedSpecialties = createEmployeeDto.specialty_ids || [];

        // Validación 1: Verificar que todos los specialty_ids en availability estén en specialty_ids
        for (const avail of createEmployeeDto.availability) {
          if (
            avail.specialty_id &&
            !assignedSpecialties.includes(avail.specialty_id)
          ) {
            throw new ConflictException(
              `La especialidad ${avail.specialty_id} en availability no está asignada al empleado`,
            );
          }
        }

        // Validación 2: Verificar que specialty_ids usados en availability coincidan con los asignados
        const availabilitySpecialtyIds = createEmployeeDto.availability
          .filter((a) => a.specialty_id !== undefined)
          .map((a) => a.specialty_id!);
        const uniqueAvailSpecIds = [...new Set(availabilitySpecialtyIds)];

        const missingSpecialties = assignedSpecialties.filter(
          (specId) => !uniqueAvailSpecIds.includes(specId),
        );

        if (missingSpecialties.length > 0) {
          throw new ConflictException(
            `Las especialidades ${missingSpecialties.join(', ')} están asignadas pero no tienen horarios de disponibilidad`,
          );
        }

        // Validación 3: Verificar que no haya traslapes de horarios
        for (let i = 0; i < createEmployeeDto.availability.length; i++) {
          const avail1 = createEmployeeDto.availability[i];
          const start1 = this.timeToMinutes(avail1.start_time);
          const end1 = this.timeToMinutes(avail1.end_time);

          for (let j = i + 1; j < createEmployeeDto.availability.length; j++) {
            const avail2 = createEmployeeDto.availability[j];

            // Solo verificar traslapes si es el mismo día y especialidad
            if (
              avail1.day_of_week === avail2.day_of_week &&
              avail1.specialty_id === avail2.specialty_id
            ) {
              const start2 = this.timeToMinutes(avail2.start_time);
              const end2 = this.timeToMinutes(avail2.end_time);

              // Verificar traslape: (start1 < end2) && (start2 < end1)
              if (start1 < end2 && start2 < end1) {
                throw new ConflictException(
                  `Conflicto de horarios: ${avail1.start_time}-${avail1.end_time} y ${avail2.start_time}-${avail2.end_time} se traslapan el día ${avail1.day_of_week} para la especialidad ${avail1.specialty_id || 'general'}`,
                );
              }
            }
          }
        }

        const availabilityRecords = createEmployeeDto.availability.map(
          (avail) => ({
            employee_id: employee.id,
            day_of_week: avail.day_of_week,
            start_time: avail.start_time,
            end_time: avail.end_time,
            specialty_id: avail.specialty_id ?? null,
            is_active: true,
          }),
        );

        await this.employeeAvailabilityModel
          .query(trx)
          .insert(availabilityRecords);
      }

      await trx.commit();

      // Enviar correo con credenciales
      try {
        await this.mailService.sendMail({
          to: createEmployeeDto.email,
          subject: 'Bienvenido a PsiFirm - Credenciales de Acceso',
          text: `Hola ${createEmployeeDto.first_name},\n\nTu cuenta de empleado ha sido creada exitosamente en PsiFirm.\n\nTus credenciales de acceso son:\nEmail: ${createEmployeeDto.email}\nContraseña: ${generatedPassword}\n\nPor favor, cambia tu contraseña después de iniciar sesión por primera vez.\n\nSaludos,\nEquipo PsiFirm`,
        });
      } catch (error) {
        console.error('Error al enviar correo:', error);
      }

      // Retornar empleado con usuario
      const createdEmployee = await this.employeeModel
        .query()
        .findById(employee.id)
        .withGraphFetched('user.role');

      return createdEmployee;
    } catch (error) {
      await trx.rollback();
      throw error;
    }
  }

  private generatePassword(): string {
    const length = 12;
    const charset =
      'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*';
    let password = '';
    const randomBytes = crypto.randomBytes(length);

    for (let i = 0; i < length; i++) {
      password += charset[randomBytes[i] % charset.length];
    }

    return password;
  }

  private timeToMinutes(time: string): number {
    const [hours, minutes] = time.split(':').map(Number);
    return hours * 60 + minutes;
  }
}
