import {
  Injectable,
  CanActivate,
  ExecutionContext,
  ForbiddenException,
} from '@nestjs/common';
import { Reflector } from '@nestjs/core';
import { PERMISSIONS_KEY } from 'src/core/decorators/permissions.decorator';
import {
  JwtAccessPayload,
  JwtStrategyRetrun,
} from '../strategies/jwt.strategy';

@Injectable()
export class PermissionsGuard implements CanActivate {
  constructor(private reflector: Reflector) {}

  canActivate(context: ExecutionContext): boolean {
    const requiredPermissions = this.reflector.getAllAndOverride<string[]>(
      PERMISSIONS_KEY,
      [context.getHandler(), context.getClass()],
    );

    if (!requiredPermissions) {
      return true; // No se requiere permiso específico
    }

    const request = context.switchToHttp().getRequest<{
      user: JwtStrategyRetrun;
    }>();
    const user: JwtStrategyRetrun = request.user; // Obtenido desde el AuthGuard

    // Se asume que el JWT tiene un array de permisos
    const userPermissions = user.permissions || [];

    const hasPermission = requiredPermissions.every((permission) =>
      userPermissions.includes(permission),
    );

    if (!hasPermission) {
      throw new ForbiddenException('Permisos insuficientes');
    }

    return true;
  }
}
