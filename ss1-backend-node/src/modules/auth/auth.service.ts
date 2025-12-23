import { Injectable, UnauthorizedException } from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import * as bcrypt from 'bcrypt';
import { randomInt } from 'crypto';
import { MailService } from '../mail/mailtrap.service';
import { UserModel } from '../users/entities/user.entity';
import { UsersService } from '../users/users.service';

type TwoFaPurpose = 'login' | 'enable' | 'disable';

interface TwoFaJwtPayload {
  sub: number;
  type: '2fa';
  purpose: TwoFaPurpose;
}

interface PartialUserUpdate {
  last_login_at?: string;
  two_fa_secret?: string | null;
  two_fa_expires_at?: string | null;
  two_fa_attempts?: number;
  two_fa_enabled?: boolean;
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
    return {
      id: user.id,
      email: user.email,
      username: user.username,
      roleId: user.role_id,
      twoFaEnabled: user.two_fa_enabled,
    };
  }

  async updateLastLogin(userId: number) {
    await this.usersService.update(userId, {
      last_login_at: new Date().toISOString(),
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
      two_fa_expires_at: expires.toISOString(),
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
      throw new UnauthorizedException({
        message: 'Usuario inválido',
      });
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
    if (!user)
      throw new UnauthorizedException({
        message: 'Usuario inválido',
      });
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
}
