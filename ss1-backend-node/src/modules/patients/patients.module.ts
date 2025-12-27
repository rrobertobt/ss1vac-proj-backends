import { Module } from '@nestjs/common';
import { PatientsService } from './patients.service';
import { PatientsController } from './patients.controller';
import { MailService } from '../mail/mailtrap.service';

@Module({
  controllers: [PatientsController],
  providers: [PatientsService, MailService],
  exports: [PatientsService],
})
export class PatientsModule {}
