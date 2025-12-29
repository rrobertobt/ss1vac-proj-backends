import { Module } from '@nestjs/common';
import { ReportsController } from './reports.controller';
import { ReportsService } from './reports.service';
import { InvoiceModel } from './entities/invoice.entity';
import { PaymentModel } from './entities/payment.entity';
import { PayrollRecordModel } from './entities/payroll-record.entity';
import { AppointmentModel } from '../appointments/entities/appointment.entity';

@Module({
  controllers: [ReportsController],
  providers: [
    ReportsService,
    {
      provide: 'InvoiceModel',
      useValue: InvoiceModel,
    },
    {
      provide: 'PaymentModel',
      useValue: PaymentModel,
    },
    {
      provide: 'PayrollRecordModel',
      useValue: PayrollRecordModel,
    },
    {
      provide: 'AppointmentModel',
      useValue: AppointmentModel,
    },
  ],
  exports: [ReportsService],
})
export class ReportsModule {}
