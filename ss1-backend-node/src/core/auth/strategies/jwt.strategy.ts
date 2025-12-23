import { PassportStrategy } from '@nestjs/passport';
import { ExtractJwt, Strategy } from 'passport-jwt';
import { Injectable, UnauthorizedException } from '@nestjs/common';
import { UsersService } from 'src/modules/users/users.service';

interface JwtAccessPayload {
  sub: number;
  email: string;
  username?: string;
  roleId: number;
  iat?: number;
  exp?: number;
}

@Injectable()
export class JwtStrategy extends PassportStrategy(Strategy, 'jwt') {
  constructor(private readonly usersService: UsersService) {
    const secret = process.env.JWT_ACCESS_SECRET;
    if (!secret) {
      throw new Error(
        'JWT_ACCESS_SECRET is not defined in environment variables',
      );
    }

    super({
      jwtFromRequest: ExtractJwt.fromAuthHeaderAsBearerToken(),
      ignoreExpiration: false,
      secretOrKey: secret,
    });
  }

  async validate(payload: JwtAccessPayload) {
    const user = await this.usersService.findById(payload.sub);
    if (!user || !user.is_active)
      throw new UnauthorizedException('Token inválido');
    // lo que retornas aquí queda como req.user
    return {
      id: user.id,
      email: user.email,
      username: user.username,
      roleId: user.role_id,
      roleName: user.role?.name ?? null,
      roleLabel: user.role?.label ?? null,
      twoFaEnabled: user.two_fa_enabled,
    };
  }
}
