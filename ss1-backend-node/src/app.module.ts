import { MailerModule } from '@nestjs-modules/mailer';
import { Module } from '@nestjs/common';
import { MailtrapTransport } from 'mailtrap';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { DatabaseConfigurationModule } from './core/database/database-configuration.module';
import { DatabaseTransactionModule } from './core/database/transaction/database-transaction.module';
import { AuthModule } from './modules/auth/auth.module';
import { UsersModule } from './modules/users/users.module';
import { RolesModule } from './modules/roles/roles.module';
import { PermissionsModule } from './modules/permissions/permissions.module';
import { EmployeesModule } from './modules/employees/employees.module';
import { PatientsModule } from './modules/patients/patients.module';
import { AreasModule } from './modules/areas/areas.module';
import { SpecialtiesModule } from './modules/specialties/specialties.module';
import { AppointmentsModule } from './modules/appointments/appointments.module';

@Module({
  imports: [
    MailerModule.forRoot({
      transport: MailtrapTransport({
        token: process.env.MAILTRAP_TOKEN || '',
      }),
    }),
    DatabaseConfigurationModule,
    DatabaseTransactionModule,
    AuthModule,
    UsersModule,
    RolesModule,
    PermissionsModule,
    EmployeesModule,
    PatientsModule,
    AreasModule,
    SpecialtiesModule,
    AppointmentsModule,
  ],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}
