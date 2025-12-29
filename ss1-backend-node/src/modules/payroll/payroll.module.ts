import { Module } from '@nestjs/common';
import { PayrollController } from './payroll.controller';
import { PayrollService } from './payroll.service';
import { AppointmentModel } from '../appointments/entities/appointment.entity';

@Module({
  controllers: [PayrollController],
  providers: [
    PayrollService,
    {
      provide: 'AppointmentModel',
      useValue: AppointmentModel,
    },
  ],
  exports: [PayrollService],
})
export class PayrollModule {}
