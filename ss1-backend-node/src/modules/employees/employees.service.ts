import {
  ConflictException,
  Inject,
  Injectable,
  NotFoundException,
} from '@nestjs/common';
import * as bcrypt from 'bcrypt';
import * as crypto from 'crypto';
import { type ModelClass } from 'objection';
import { MailService } from '../mail/mailtrap.service';
import { UserModel } from '../users/entities/user.entity';
import { CreateEmployeeDto } from './dto/create-employee.dto';
import { UpdateEmployeeDto } from './dto/update-employee.dto';
import { EmployeeModel } from './entities/employee.entity';
import { EmployeeAvailabilityModel } from './entities/employee-availability.entity';
import { FilterEmployeesDto } from './dto/filter-employees.dto';

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

            // Solo verificar traslapes si es el mismo día (sin importar especialidad)
            if (avail1.day_of_week === avail2.day_of_week) {
              const start2 = this.timeToMinutes(avail2.start_time);
              const end2 = this.timeToMinutes(avail2.end_time);

              // Verificar traslape: (start1 < end2) && (start2 < end1)
              if (start1 < end2 && start2 < end1) {
                throw new ConflictException(
                  `Conflicto de horarios: ${avail1.start_time}-${avail1.end_time} y ${avail2.start_time}-${avail2.end_time} se traslapan el día ${avail1.day_of_week}`,
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

  async findAll(filters: FilterEmployeesDto) {
    const { page = 1, limit = 10, area_id, role_id, status, search } = filters;
    const offset = (page - 1) * limit;

    let query = this.employeeModel
      .query()
      .withGraphFetched('user.role')
      .orderBy('employees.created_at', 'desc');

    // Join con users si necesitamos filtrar por role_id
    if (role_id !== undefined) {
      query = query.joinRelated('user').where('user.role_id', role_id);
    }

    // Filtros
    if (area_id !== undefined) {
      query = query.where('employees.area_id', area_id);
    }

    if (status !== undefined) {
      query = query.where('employees.status', status);
    }

    if (search) {
      query = query.where((builder) => {
        builder
          .where('employees.first_name', 'ilike', `%${search}%`)
          .orWhere('employees.last_name', 'ilike', `%${search}%`)
          .orWhere('employees.license_number', 'ilike', `%${search}%`);
      });
    }

    const [employees, total] = await Promise.all([
      query.limit(limit).offset(offset),
      query.resultSize(),
    ]);

    return {
      data: employees,
      meta: {
        total,
        page,
        limit,
        totalPages: Math.ceil(total / limit),
      },
    };
  }

  async findOne(id: number) {
    const employee = await this.employeeModel
      .query()
      .findById(id)
      .withGraphFetched('[user.role, area, specialties, availability]');

    if (!employee) {
      throw new NotFoundException('Empleado no encontrado');
    }

    return employee;
  }

  async update(id: number, updateEmployeeDto: UpdateEmployeeDto) {
    // Verificar que el empleado existe
    const employee = await this.employeeModel
      .query()
      .findById(id)
      .withGraphFetched('user');

    if (!employee) {
      throw new NotFoundException('Empleado no encontrado');
    }

    // Verificar email único si se está actualizando
    if (
      updateEmployeeDto.email &&
      updateEmployeeDto.email !== employee.user?.email
    ) {
      const existingUser = await this.userModel
        .query()
        .where('email', updateEmployeeDto.email)
        .first();

      if (existingUser) {
        throw new ConflictException('El email ya está registrado');
      }
    }

    // Verificar username único si se está actualizando
    if (
      updateEmployeeDto.username &&
      updateEmployeeDto.username !== employee.user?.username
    ) {
      const existingUsername = await this.userModel
        .query()
        .where('username', updateEmployeeDto.username)
        .first();

      if (existingUsername) {
        throw new ConflictException('El username ya está registrado');
      }
    }

    // Iniciar transacción
    const trx = await this.userModel.startTransaction();

    try {
      // Actualizar usuario si hay cambios
      if (
        employee.user_id &&
        (updateEmployeeDto.email ||
          updateEmployeeDto.username ||
          updateEmployeeDto.role_id)
      ) {
        const userUpdates: any = {};
        if (updateEmployeeDto.email)
          userUpdates.email = updateEmployeeDto.email;
        if (updateEmployeeDto.username)
          userUpdates.username = updateEmployeeDto.username;
        if (updateEmployeeDto.role_id)
          userUpdates.role_id = updateEmployeeDto.role_id;

        await this.userModel
          .query(trx)
          .patchAndFetchById(employee.user_id, userUpdates);
      }

      // Actualizar empleado
      const employeeUpdates: any = {};
      if (updateEmployeeDto.first_name !== undefined)
        employeeUpdates.first_name = updateEmployeeDto.first_name;
      if (updateEmployeeDto.last_name !== undefined)
        employeeUpdates.last_name = updateEmployeeDto.last_name;
      if (updateEmployeeDto.license_number !== undefined)
        employeeUpdates.license_number = updateEmployeeDto.license_number;
      if (updateEmployeeDto.area_id !== undefined)
        employeeUpdates.area_id = updateEmployeeDto.area_id;
      if (updateEmployeeDto.base_salary !== undefined)
        employeeUpdates.base_salary = updateEmployeeDto.base_salary;
      if (updateEmployeeDto.session_rate !== undefined)
        employeeUpdates.session_rate = updateEmployeeDto.session_rate;
      if (updateEmployeeDto.igss_percentage !== undefined)
        employeeUpdates.igss_percentage = updateEmployeeDto.igss_percentage;
      if (updateEmployeeDto.hired_at !== undefined) {
        employeeUpdates.hired_at = updateEmployeeDto.hired_at
          ? new Date(updateEmployeeDto.hired_at)
          : null;
      }

      if (Object.keys(employeeUpdates).length > 0) {
        await this.employeeModel
          .query(trx)
          .patchAndFetchById(id, employeeUpdates);
      }

      // Actualizar especialidades si se proporcionaron
      if (updateEmployeeDto.specialty_ids !== undefined) {
        // Eliminar especialidades existentes
        await this.employeeAvailabilityModel
          .knex()
          .raw('DELETE FROM employee_specialties WHERE employee_id = ?', [id])
          .transacting(trx);

        // Insertar nuevas especialidades
        if (updateEmployeeDto.specialty_ids.length > 0) {
          const specialtyRecords = updateEmployeeDto.specialty_ids.map(
            (specialtyId) => ({
              employee_id: id,
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
      }

      // Actualizar disponibilidad si se proporcionó
      if (updateEmployeeDto.availability !== undefined) {
        const assignedSpecialties = updateEmployeeDto.specialty_ids || [];

        // Solo validar si hay especialidades y disponibilidad
        if (
          updateEmployeeDto.availability.length > 0 &&
          assignedSpecialties.length > 0
        ) {
          // Validación 1: Verificar que todos los specialty_ids en availability estén en specialty_ids
          for (const avail of updateEmployeeDto.availability) {
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
          const availabilitySpecialtyIds = updateEmployeeDto.availability
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
        }

        // Validación 3: Verificar que no haya traslapes de horarios
        if (updateEmployeeDto.availability.length > 0) {
          for (let i = 0; i < updateEmployeeDto.availability.length; i++) {
            const avail1 = updateEmployeeDto.availability[i];
            const start1 = this.timeToMinutes(avail1.start_time);
            const end1 = this.timeToMinutes(avail1.end_time);

            for (
              let j = i + 1;
              j < updateEmployeeDto.availability.length;
              j++
            ) {
              const avail2 = updateEmployeeDto.availability[j];

              // Solo verificar traslapes si es el mismo día (sin importar especialidad)
              if (avail1.day_of_week === avail2.day_of_week) {
                const start2 = this.timeToMinutes(avail2.start_time);
                const end2 = this.timeToMinutes(avail2.end_time);

                if (start1 < end2 && start2 < end1) {
                  throw new ConflictException(
                    `Conflicto de horarios: ${avail1.start_time}-${avail1.end_time} y ${avail2.start_time}-${avail2.end_time} se traslapan el día ${avail1.day_of_week}`,
                  );
                }
              }
            }
          }
        }

        // Eliminar disponibilidad existente
        await this.employeeAvailabilityModel
          .query(trx)
          .where('employee_id', id)
          .delete();

        // Insertar nueva disponibilidad
        if (updateEmployeeDto.availability.length > 0) {
          const availabilityRecords = updateEmployeeDto.availability.map(
            (avail) => ({
              employee_id: id,
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
      }

      await trx.commit();

      // Retornar empleado actualizado
      const updatedEmployee = await this.employeeModel
        .query()
        .findById(id)
        .withGraphFetched('user.role');

      return updatedEmployee;
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
