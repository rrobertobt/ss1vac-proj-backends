import { Module } from '@nestjs/common';
import { EmployeesService } from './employees.service';
import { EmployeesController } from './employees.controller';
import { MailService } from '../mail/mailtrap.service';

@Module({
  controllers: [EmployeesController],
  providers: [EmployeesService, MailService],
  exports: [EmployeesService],
})
export class EmployeesModule {}
