import { ConflictException, Inject, Injectable } from '@nestjs/common';
import * as bcrypt from 'bcrypt';
import * as crypto from 'crypto';
import { type ModelClass } from 'objection';
import { MailService } from '../mail/mailtrap.service';
import { UserModel } from '../users/entities/user.entity';
import { CreateEmployeeDto } from './dto/create-employee.dto';
import { EmployeeModel } from './entities/employee.entity';

@Injectable()
export class EmployeesService {
  constructor(
    @Inject(EmployeeModel.name)
    private employeeModel: ModelClass<EmployeeModel>,
    @Inject(UserModel.name) private userModel: ModelClass<UserModel>,
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
}
