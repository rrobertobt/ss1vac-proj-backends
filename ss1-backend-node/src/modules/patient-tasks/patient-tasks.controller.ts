import {
  Controller,
  Post,
  Patch,
  Get,
  Body,
  Param,
  UseGuards,
  ParseIntPipe,
  Request,
} from '@nestjs/common';
import { PatientTasksService } from './patient-tasks.service';
import { CreatePatientTaskDto } from './dto/create-patient-task.dto';
import { UpdatePatientTaskDto } from './dto/update-patient-task.dto';
import { JwtAuthGuard } from 'src/core/auth/guards/jwt-auth.guard';
import { PermissionsGuard } from 'src/core/auth/guards/permissions.guard';
import { Permissions } from 'src/core/decorators/permissions.decorator';
import { Permission } from 'src/core/enums/permissions.enum';

@Controller()
@UseGuards(JwtAuthGuard, PermissionsGuard)
export class PatientTasksController {
  constructor(private readonly patientTasksService: PatientTasksService) {}

  @Post('patients/:patientId/tasks')
  @Permissions(Permission.ASSIGN_PATIENT_TASKS)
  create(
    @Param('patientId', ParseIntPipe) patientId: number,
    @Body() createDto: CreatePatientTaskDto,
    @Request() req,
  ) {
    return this.patientTasksService.create(patientId, createDto, req.user);
  }

  @Get('patients/me/tasks')
  @UseGuards(JwtAuthGuard)
  findMyTasks(@Request() req) {
    return this.patientTasksService.findByCurrentPatient(req.user);
  }

  @Get('patients/:patientId/tasks')
  @Permissions(Permission.VIEW_PATIENTS)
  findByPatient(@Param('patientId', ParseIntPipe) patientId: number) {
    return this.patientTasksService.findByPatient(patientId);
  }

  @Patch('patient-tasks/:taskId')
  update(
    @Param('taskId', ParseIntPipe) taskId: number,
    @Body() updateDto: UpdatePatientTaskDto,
  ) {
    return this.patientTasksService.update(taskId, updateDto);
  }
}
