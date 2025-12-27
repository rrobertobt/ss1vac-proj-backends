import { ConflictException, Inject, Injectable } from '@nestjs/common';
import { CreatePatientDto } from './dto/create-patient.dto';
import { PatientModel } from './entities/patient.entity';
import { UserModel } from '../users/entities/user.entity';
import { RoleModel } from '../roles/entities/role.entity';
import { MailService } from '../mail/mailtrap.service';
import { type ModelClass } from 'objection';
import * as bcrypt from 'bcrypt';
import * as crypto from 'crypto';

@Injectable()
export class PatientsService {
  constructor(
    @Inject(PatientModel.name) private patientModel: ModelClass<PatientModel>,
    @Inject(UserModel.name) private userModel: ModelClass<UserModel>,
    @Inject(RoleModel.name) private roleModel: ModelClass<RoleModel>,
    private readonly mailService: MailService,
  ) {}

  async create(createPatientDto: CreatePatientDto) {
    const trx = await this.patientModel.startTransaction();

    try {
      let userId: number | null = null;

      // Si se proporciona email, crear usuario con rol de paciente
      if (createPatientDto.email) {
        // Verificar si el email ya existe
        const existingUser = await this.userModel
          .query(trx)
          .where('email', createPatientDto.email)
          .first();

        if (existingUser) {
          throw new ConflictException('El email ya está registrado');
        }

        // Verificar si el username ya existe (si se proporcionó)
        if (createPatientDto.username) {
          const existingUsername = await this.userModel
            .query(trx)
            .where('username', createPatientDto.username)
            .first();

          if (existingUsername) {
            throw new ConflictException('El username ya está registrado');
          }
        }

        // Buscar el rol de PATIENT
        const patientRole = await this.roleModel
          .query(trx)
          .where('name', 'PATIENT')
          .first();

        if (!patientRole) {
          throw new Error('Rol de PATIENT no encontrado en el sistema');
        }

        // Generar contraseña aleatoria
        const generatedPassword = this.generatePassword();
        const hashedPassword = await bcrypt.hash(generatedPassword, 10);

        // Crear usuario
        const user = await this.userModel.query(trx).insert({
          email: createPatientDto.email,
          username: createPatientDto.username,
          password_hash: hashedPassword,
          role_id: patientRole.id,
          is_active: true,
        });

        userId = user.id;

        // Enviar correo con credenciales
        try {
          await this.mailService.sendMail({
            to: createPatientDto.email,
            subject: 'Bienvenido a PsiFirm - Portal de Pacientes',
            text: `Hola ${createPatientDto.first_name},\n\nTu cuenta de paciente ha sido creada exitosamente en PsiFirm.\n\nTus credenciales de acceso son:\nEmail: ${createPatientDto.email}\nContraseña: ${generatedPassword}\n\nPuedes acceder al portal de pacientes para ver tu información y citas.\n\nPor favor, cambia tu contraseña después de iniciar sesión por primera vez.\n\nSaludos,\nEquipo PsiFirm`,
          });
        } catch (error) {
          console.error('Error al enviar correo:', error);
        }
      }

      // Crear paciente
      const patient = await this.patientModel.query(trx).insert({
        user_id: userId,
        first_name: createPatientDto.first_name,
        last_name: createPatientDto.last_name,
        dob: createPatientDto.dob ? new Date(createPatientDto.dob) : null,
        gender: createPatientDto.gender,
        marital_status: createPatientDto.marital_status,
        occupation: createPatientDto.occupation,
        education_level: createPatientDto.education_level,
        address: createPatientDto.address,
        phone: createPatientDto.phone,
        email: createPatientDto.patient_email || createPatientDto.email,
        emergency_contact_name: createPatientDto.emergency_contact_name,
        emergency_contact_relationship:
          createPatientDto.emergency_contact_relationship,
        emergency_contact_phone: createPatientDto.emergency_contact_phone,
        status: 'ACTIVE',
      });

      await trx.commit();

      // Retornar paciente con usuario si existe
      const createdPatient = await this.patientModel
        .query()
        .findById(patient.id)
        .withGraphFetched('user.role');

      return createdPatient;
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
