import {
  Body,
  Controller,
  Post,
  Req,
  UseGuards,
  UnauthorizedException,
  Get,
} from '@nestjs/common';
import { type Request } from 'express';
import { AuthService } from './auth.service';
import { LocalAuthGuard } from 'src/core/auth/guards/local-auth.guard';
import { JwtAuthGuard } from 'src/core/auth/guards/jwt-auth.guard';
import { TwoFaVerifyDto } from './dto/twofa-verify.dto';
import { UserModel } from '../users/entities/user.entity';

interface JwtUser {
  id: number;
  email: string;
  username: string;
  roleId: number;
  roleName: string | null;
  twoFaEnabled: boolean;
}

interface AuthenticatedRequest extends Request {
  user: UserModel;
}

interface JwtAuthenticatedRequest extends Request {
  user: JwtUser;
}

@Controller('auth')
export class AuthController {
  constructor(private readonly authService: AuthService) {}

  /**
   * Login (factor 1: password)
   * - Si el usuario NO tiene 2FA activo => devuelve accessToken.
   * - Si tiene 2FA activo => envía correo con código y devuelve challengeId.
   */
  @UseGuards(LocalAuthGuard)
  @Post('login')
  async login(@Req() req: AuthenticatedRequest) {
    const user = req.user;
    if (!user?.id) throw new UnauthorizedException('Credenciales inválidas');

    // si NO hay 2FA
    if (!user.two_fa_enabled) {
      const accessToken = await this.authService.issueAccessToken(user);
      await this.authService.updateLastLogin(user.id);
      return {
        accessToken,
        user: this.authService.publicUser(user),
      };
    }

    // si SÍ hay 2FA
    const challengeId = await this.authService.startTwoFaLogin(user.id);
    return { twoFaRequired: true, challengeId };
  }

  /**
   * Verifica código 2FA (factor 2)
   * Body: { challengeId, code }
   * - Si válido => devuelve accessToken.
   */
  @Post('2fa/verify')
  async verifyTwoFa(@Body() dto: TwoFaVerifyDto) {
    const result = await this.authService.verifyTwoFaCode(
      dto.challengeId,
      dto.code,
    );
    if (!result.ok) throw new UnauthorizedException(result.reason);

    const accessToken = await this.authService.issueAccessToken(result.user);
    await this.authService.updateLastLogin(result.user.id);

    return {
      accessToken,
      user: this.authService.publicUser(result.user),
    };
  }

  /**
   * Request para activar 2FA (requiere JWT ya logueado)
   * Devuelve challengeId para confirmar.
   */
  @UseGuards(JwtAuthGuard)
  @Post('2fa/enable/request')
  async requestEnableTwoFa(@Req() req: JwtAuthenticatedRequest) {
    const userId = req.user.id;
    const challengeId = await this.authService.startTwoFaToggle(
      userId,
      'enable',
    );
    return { challengeId };
  }

  /**
   * Confirmar activar 2FA
   */
  @UseGuards(JwtAuthGuard)
  @Post('2fa/enable/confirm')
  async confirmEnableTwoFa(
    @Req() req: JwtAuthenticatedRequest,
    @Body() dto: TwoFaVerifyDto,
  ) {
    const userId = req.user.id;
    const result = await this.authService.confirmTwoFaToggle(
      userId,
      dto.challengeId,
      dto.code,
      'enable',
    );
    if (!result.ok) throw new UnauthorizedException(result.reason);
    return { twoFaEnabled: true };
  }

  /**
   * Request para desactivar 2FA (con confirm por correo)
   */
  @UseGuards(JwtAuthGuard)
  @Post('2fa/disable/request')
  async requestDisableTwoFa(@Req() req: JwtAuthenticatedRequest) {
    const userId = req.user.id;
    const challengeId = await this.authService.startTwoFaToggle(
      userId,
      'disable',
    );
    return { challengeId };
  }

  /**
   * Confirmar desactivar 2FA
   */
  @UseGuards(JwtAuthGuard)
  @Post('2fa/disable/confirm')
  async confirmDisableTwoFa(
    @Req() req: JwtAuthenticatedRequest,
    @Body() dto: TwoFaVerifyDto,
  ) {
    const userId = req.user.id;
    const result = await this.authService.confirmTwoFaToggle(
      userId,
      dto.challengeId,
      dto.code,
      'disable',
    );
    if (!result.ok) throw new UnauthorizedException(result.reason);
    return { twoFaEnabled: false };
  }

  @UseGuards(JwtAuthGuard)
  @Get('/me')
  getProfile(@Req() req: JwtAuthenticatedRequest) {
    return {
      user: {
        id: req.user.id,
        email: req.user.email,
        username: req.user.username,
        roleId: req.user.roleId,
        roleName: req.user.roleName,
        twoFaEnabled: req.user.twoFaEnabled,
      },
    };
  }
}
