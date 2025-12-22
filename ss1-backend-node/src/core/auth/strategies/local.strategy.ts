import { Strategy } from 'passport-local';
import { PassportStrategy } from '@nestjs/passport';
import { Injectable, UnauthorizedException } from '@nestjs/common';
import { AuthService } from 'src/modules/auth/auth.service';

@Injectable()
export class LocalStrategy extends PassportStrategy(Strategy, 'local') {
  constructor(private readonly authService: AuthService) {
    // Usamos "emailOrUsername" como usernameField
    super({ usernameField: 'emailOrUsername', passwordField: 'password' });
  }

  async validate(emailOrUsername: string, password: string) {
    const user = await this.authService.validateUser(emailOrUsername, password);
    if (!user) throw new UnauthorizedException('Credenciales inválidas');
    return user; // queda en req.user
  }
}
