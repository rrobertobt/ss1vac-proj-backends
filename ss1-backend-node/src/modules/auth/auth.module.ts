import { Module } from '@nestjs/common';
import { AuthController } from './auth.controller';
import { AuthService } from './auth.service';
import { JwtModule } from '@nestjs/jwt';
import { UsersModule } from '../users/users.module';
import { LocalStrategy } from 'src/core/auth/strategies/local.strategy';
import { JwtStrategy } from 'src/core/auth/strategies/jwt.strategy';
import { SesMailService } from '../mail/ses-mail.service';
import { MailService } from '../mail/mailtrap.service';

@Module({
  imports: [
    UsersModule,
    JwtModule.register({
      global: true,
      secret: process.env.JWT_ACCESS_SECRET,
      signOptions: {
        expiresIn: parseInt(process.env.TOKEN_EXPIRATION ?? '24h'),
      },
    }),
  ],
  controllers: [AuthController],
  providers: [AuthService, LocalStrategy, JwtStrategy, MailService],
  exports: [AuthService],
})
export class AuthModule {}
