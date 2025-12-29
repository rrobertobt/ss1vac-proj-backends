import {
  Injectable,
  UnauthorizedException,
  ConflictException,
  Inject,
} from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import * as bcrypt from 'bcrypt';
import { randomInt } from 'crypto';
import { MailService } from '../mail/mailtrap.service';
import { UserModel } from '../users/entities/user.entity';
import { UsersService } from '../users/users.service';
import { UpdateProfileDto } from './dto/update-profile.dto';
import { PatientModel } from '../patients/entities/patient.entity';
import type { ModelClass } from 'objection';

type TwoFaPurpose = 'login' | 'enable' | 'disable';

interface TwoFaJwtPayload {
  sub: number;
  type: '2fa';
  purpose: TwoFaPurpose;
}

interface PartialUserUpdate {
  last_login_at?: Date | null;
  two_fa_secret?: string | null;
  two_fa_expires_at?: Date | null;
  two_fa_attempts?: number;
  two_fa_enabled?: boolean;
  password_reset_token?: string | null;
  password_reset_expires?: string | null;
  password_hash?: string;
}

@Injectable()
export class AuthService {
  constructor(
    private readonly usersService: UsersService,
    private readonly jwt: JwtService,
    private readonly mail: MailService,
  ) {}

  // --- LocalStrategy usa esto ---
  async validateUser(emailOrUsername: string, password: string) {
    const user = await this.usersService.findByEmailOrUsername(emailOrUsername);
    if (!user || !user.is_active) return null;

    const ok = await bcrypt.compare(password, user.password_hash ?? '');
    if (!ok) return null;

    return user;
  }

  // --- Access JWT ---
  async issueAccessToken(user: UserModel): Promise<string> {
    const payload = {
      sub: user.id,
      email: user.email,
      username: user.username,
      roleId: user.role_id,
    };

    // "expira en bastante tiempo": configúralo por env, ej: 7d, 30d, etc.
    return this.jwt.signAsync(payload);
  }

  publicUser(user: UserModel) {
    // Extraer códigos de permisos del rol
    const permissions = user.role?.permissions?.map((p) => p.code) ?? [];

    return {
      id: user.id,
      email: user.email,
      username: user.username,
      role_id: user.role_id,
      role_name: user.role?.name ?? null,
      role_label: user.role?.label ?? null,
      two_fa_enabled: user.two_fa_enabled,
      permissions,
      employee: user.employee
        ? {
            id: user.employee.id,
            first_name: user.employee.first_name,
            last_name: user.employee.last_name,
            license_number: user.employee.license_number,
            status: user.employee.status,
          }
        : null,
      patient: user.patient
        ? {
            id: user.patient.id,
            first_name: user.patient.first_name,
            last_name: user.patient.last_name,
            dob: user.patient.dob,
            phone: user.patient.phone,
            email: user.patient.email,
            status: user.patient.status,
          }
        : null,
    };
  }

  async updateLastLogin(userId: number) {
    await this.usersService.update(userId, {
      last_login_at: new Date(),
    });
  }

  // --- 2FA: generar y enviar código ---
  private generateCode(): string {
    // 6 dígitos, con ceros a la izquierda
    const n = randomInt(0, 1_000_000);
    return n.toString().padStart(6, '0');
  }

  private async storeTwoFaCode(userId: number, code: string, ttlMinutes = 10) {
    const codeHash = await bcrypt.hash(code, 10);
    const expires = new Date(Date.now() + ttlMinutes * 60 * 1000);

    const updateData: PartialUserUpdate = {
      two_fa_secret: codeHash,
      two_fa_expires_at: expires,
      two_fa_attempts: 0,
    };

    await this.usersService.update(userId, updateData);
  }

  private async sendTwoFaEmail(
    to: string,
    code: string,
    purpose: TwoFaPurpose,
  ) {
    const subjectMap: Record<TwoFaPurpose, string> = {
      login: 'Tu código de verificación',
      enable: 'Código para activar 2FA',
      disable: 'Código para desactivar 2FA',
    };

    const subject = subjectMap[purpose];
    const text = `Tu código es: ${code}\n\nEste código expira en pocos minutos.`;

    await this.mail.sendMail({
      to,
      subject,
      text,
    });
  }

  // --- ChallengeId: JWT temporal (NO access token) ---
  private async issueTwoFaChallenge(
    userId: number,
    purpose: TwoFaPurpose,
  ): Promise<string> {
    return this.jwt.signAsync({ sub: userId, type: '2fa', purpose });
  }

  private verifyTwoFaChallenge(
    challengeId: string,
  ): { userId: number; purpose: TwoFaPurpose } | null {
    try {
      const payload = this.jwt.verify<TwoFaJwtPayload>(challengeId);
      if (!payload || payload.type !== '2fa') return null;
      return { userId: payload.sub, purpose: payload.purpose };
    } catch {
      return null;
    }
  }

  // --- Login flow con 2FA ---
  async startTwoFaLogin(userId: number): Promise<string> {
    const user = await this.usersService.findById(userId);
    if (!user || !user.is_active)
      throw new UnauthorizedException('Usuario inválido');
    const code = this.generateCode();

    await this.storeTwoFaCode(userId, code, 10);
    await this.sendTwoFaEmail(user.email, code, 'login');

    return this.issueTwoFaChallenge(userId, 'login');
  }

  async verifyTwoFaCode(
    challengeId: string,
    code: string,
  ): Promise<{ ok: true; user: UserModel } | { ok: false; reason: string }> {
    const challenge = this.verifyTwoFaChallenge(challengeId);
    if (!challenge || challenge.purpose !== 'login')
      return { ok: false, reason: 'Challenge inválido o expirado' };

    const user = await this.usersService.findById(challenge.userId);
    if (!user || !user.is_active)
      return { ok: false, reason: 'Usuario inválido' };

    // validar expiración
    if (!user.two_fa_expires_at)
      return { ok: false, reason: 'Código no solicitado' };
    const expiresAt = new Date(user.two_fa_expires_at).getTime();
    if (Date.now() > expiresAt) return { ok: false, reason: 'Código expirado' };

    // intentos (si agregas two_fa_attempts)
    const attempts = Number(user.two_fa_attempts ?? 0);
    if (attempts >= 5)
      return {
        ok: false,
        reason: 'Demasiados intentos. Solicita un nuevo código.',
      };

    const ok = await bcrypt.compare(code, user.two_fa_secret ?? '');
    if (!ok) {
      const updateData: PartialUserUpdate = {
        two_fa_attempts: attempts + 1,
      };
      await this.usersService.update(user.id, updateData);
      return { ok: false, reason: 'Código inválido' };
    }

    // consumir código (one-time)
    const updateData: PartialUserUpdate = {
      two_fa_secret: null,
      two_fa_expires_at: null,
      two_fa_attempts: 0,
    };
    await this.usersService.update(user.id, updateData);

    return { ok: true, user };
  }

  // --- Enable/Disable flows ---
  async startTwoFaToggle(userId: number, action: 'enable' | 'disable') {
    const user = await this.usersService.findById(userId);
    if (!user) throw new UnauthorizedException('Usuario inválido');
    const code = this.generateCode();

    await this.storeTwoFaCode(userId, code, 10);
    await this.sendTwoFaEmail(user.email, code, action);

    return this.issueTwoFaChallenge(userId, action);
  }

  async confirmTwoFaToggle(
    userId: number,
    challengeId: string,
    code: string,
    action: 'enable' | 'disable',
  ): Promise<{ ok: true } | { ok: false; reason: string }> {
    const challenge = this.verifyTwoFaChallenge(challengeId);
    if (
      !challenge ||
      challenge.userId !== userId ||
      challenge.purpose !== action
    ) {
      return { ok: false, reason: 'Challenge inválido o expirado' };
    }

    const user = await this.usersService.findById(userId);
    if (!user) return { ok: false, reason: 'Usuario inválido' };

    // Reutilizamos la misma validación que login:
    const expiresAt = user.two_fa_expires_at
      ? new Date(user.two_fa_expires_at).getTime()
      : 0;
    if (!expiresAt || Date.now() > expiresAt)
      return { ok: false, reason: 'Código expirado' };

    const attempts = Number(user.two_fa_attempts ?? 0);
    if (attempts >= 5)
      return {
        ok: false,
        reason: 'Demasiados intentos. Solicita un nuevo código.',
      };

    const ok = await bcrypt.compare(code, user.two_fa_secret ?? '');
    if (!ok) {
      const updateData: PartialUserUpdate = {
        two_fa_attempts: attempts + 1,
      };
      await this.usersService.update(user.id, updateData);
      return { ok: false, reason: 'Código inválido' };
    }

    // aplicar cambio y consumir código
    const updateData: PartialUserUpdate = {
      two_fa_enabled: action === 'enable',
      two_fa_secret: null,
      two_fa_expires_at: null,
      two_fa_attempts: 0,
    };
    await this.usersService.update(user.id, updateData);

    return { ok: true };
  }

  // --- Password Reset ---
  async requestPasswordReset(email: string): Promise<void> {
    const user = await this.usersService.findByEmailOrUsername(email);
    // Por seguridad, no revelamos si el email existe o no
    if (!user || !user.is_active) return;

    const code = this.generateCode();
    const codeHash = await bcrypt.hash(code, 10);
    const expires = new Date(Date.now() + 15 * 60 * 1000); // 15 minutos

    const updateData: PartialUserUpdate = {
      password_reset_token: codeHash,
      password_reset_expires: expires.toISOString(),
    };
    await this.usersService.update(user.id, updateData);

    await this.mail.sendMail({
      to: user.email,
      subject: 'Código de recuperación de contraseña',
      text: `Tu código de recuperación es: ${code}\n\nEste código expira en 15 minutos.`,
    });
  }

  async resetPassword(
    email: string,
    code: string,
    newPassword: string,
  ): Promise<{ ok: true } | { ok: false; reason: string }> {
    const user = await this.usersService.findByEmailOrUsername(email);
    if (!user || !user.is_active)
      return { ok: false, reason: 'Usuario inválido' };

    if (!user.password_reset_token || !user.password_reset_expires)
      return { ok: false, reason: 'Código no solicitado' };

    const expiresAt = new Date(user.password_reset_expires).getTime();
    if (Date.now() > expiresAt) return { ok: false, reason: 'Código expirado' };

    const ok = await bcrypt.compare(code, user.password_reset_token);
    if (!ok) return { ok: false, reason: 'Código inválido' };

    // Hash de la nueva contraseña
    const passwordHash = await bcrypt.hash(newPassword, 10);

    // Actualizar contraseña y limpiar token
    const updateData: PartialUserUpdate = {
      password_hash: passwordHash,
      password_reset_token: null,
      password_reset_expires: null,
    };
    await this.usersService.update(user.id, updateData);

    return { ok: true };
  }

  // --- Change Password (usuario autenticado) ---
  async changePassword(
    userId: number,
    currentPassword: string,
    newPassword: string,
  ): Promise<{ ok: true } | { ok: false; reason: string }> {
    const user = await this.usersService.findById(userId);
    if (!user || !user.is_active)
      return { ok: false, reason: 'Usuario inválido' };

    // Verificar que la contraseña actual sea correcta
    const isCurrentPasswordValid = await bcrypt.compare(
      currentPassword,
      user.password_hash ?? '',
    );
    if (!isCurrentPasswordValid)
      return { ok: false, reason: 'Contraseña actual incorrecta' };

    // Hash de la nueva contraseña
    const passwordHash = await bcrypt.hash(newPassword, 10);

    // Actualizar contraseña
    const updateData: PartialUserUpdate = {
      password_hash: passwordHash,
    };
    await this.usersService.update(user.id, updateData);

    return { ok: true };
  }

  // --- Update Profile (datos personales) ---
  async updateProfile(
    userId: number,
    dto: UpdateProfileDto,
  ): Promise<UserModel> {
    const user = await this.usersService.findById(userId);
    if (!user || !user.is_active) {
      throw new UnauthorizedException('Usuario inválido');
    }

    const trx = await PatientModel.startTransaction();

    try {
      // Actualizar username si se proporciona
      if (dto.username !== undefined) {
        // Verificar si el nuevo username ya existe
        const existingUsername = await this.usersService.findByEmailOrUsername(
          dto.username,
          trx,
        );
        if (existingUsername && existingUsername.id !== userId) {
          throw new ConflictException('El username ya está en uso');
        }

        await this.usersService.update(userId, { username: dto.username }, trx);
      }

      // Si el usuario es paciente, actualizar datos del paciente
      if (user.patient?.id) {
        const patientUpdate: Partial<PatientModel> = {};

        // Solo incluir los campos que se proporcionaron en el DTO
        if (dto.phone !== undefined) patientUpdate.phone = dto.phone;
        if (dto.email !== undefined) patientUpdate.email = dto.email;
        if (dto.address !== undefined) patientUpdate.address = dto.address;
        if (dto.gender !== undefined) patientUpdate.gender = dto.gender;
        if (dto.marital_status !== undefined)
          patientUpdate.marital_status = dto.marital_status;
        if (dto.occupation !== undefined)
          patientUpdate.occupation = dto.occupation;
        if (dto.education_level !== undefined)
          patientUpdate.education_level = dto.education_level;
        if (dto.emergency_contact_name !== undefined)
          patientUpdate.emergency_contact_name = dto.emergency_contact_name;
        if (dto.emergency_contact_relationship !== undefined)
          patientUpdate.emergency_contact_relationship =
            dto.emergency_contact_relationship;
        if (dto.emergency_contact_phone !== undefined)
          patientUpdate.emergency_contact_phone = dto.emergency_contact_phone;

        // Si hay campos de paciente para actualizar
        if (Object.keys(patientUpdate).length > 0) {
          await PatientModel.query(trx).patchAndFetchById(
            user.patient.id,
            patientUpdate,
          );
        }
      }

      await trx.commit();

      // Retornar el usuario actualizado con todas sus relaciones
      const updatedUser = await this.usersService.findById(userId);
      if (!updatedUser) {
        throw new UnauthorizedException(
          'Error al recuperar el usuario actualizado',
        );
      }
      return updatedUser;
    } catch (error) {
      await trx.rollback();
      throw error;
    }
  }
}
