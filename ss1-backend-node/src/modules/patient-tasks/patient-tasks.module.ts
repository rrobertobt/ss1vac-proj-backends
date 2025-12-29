import { Module } from '@nestjs/common';
import { PatientTasksService } from './patient-tasks.service';
import { PatientTasksController } from './patient-tasks.controller';

@Module({
  controllers: [PatientTasksController],
  providers: [PatientTasksService],
  exports: [PatientTasksService],
})
export class PatientTasksModule {}
