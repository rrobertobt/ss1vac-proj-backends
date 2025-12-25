import { PassportStrategy } from '@nestjs/passport';
import { ExtractJwt, Strategy } from 'passport-jwt';
import { Injectable, UnauthorizedException } from '@nestjs/common';
import { UsersService } from 'src/modules/users/users.service';
import { PatientModel } from 'src/modules/patients/entities/patient.entity';
import { EmployeeModel } from 'src/modules/employees/entities/employee.entity';

export interface JwtAccessPayload {
  sub: number;
  email: string;
  username?: string;
  roleId: number;
  permissions?: string[];
  iat?: number;
  exp?: number;
}

export interface JwtStrategyRetrun {
  id: number;
  email: string;
  username: string;
  roleId: number;
  roleName: string | null;
  roleLabel: string | null;
  twoFaEnabled: boolean;
  permissions: string[];
  patient?: PatientModel;
  employee?: EmployeeModel;
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

  async validate(payload: JwtAccessPayload): Promise<JwtStrategyRetrun> {
    const user = await this.usersService.findById(payload.sub);
    console.log('JWT validate found user:', user);
    if (!user || !user.is_active)
      throw new UnauthorizedException('Token inválido');

    // Extraer códigos de permisos del rol
    const permissions = user.role?.permissions?.map((p) => p.code) ?? [];

    // lo que retornas aquí queda como req.user
    return {
      id: user.id,
      email: user.email,
      username: user.username,
      roleId: user.role_id,
      roleName: user.role?.name ?? null,
      roleLabel: user.role?.label ?? null,
      twoFaEnabled: user.two_fa_enabled,
      permissions,
      patient: user.patient,
      employee: user.employee,
    };
  }
}
