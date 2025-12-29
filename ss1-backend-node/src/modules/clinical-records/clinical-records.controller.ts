import {
  Controller,
  Post,
  Get,
  Patch,
  Body,
  Param,
  Query,
  UseGuards,
  ParseIntPipe,
  Request,
} from '@nestjs/common';
import { ClinicalRecordsService } from './clinical-records.service';
import { CreateClinicalRecordDto } from './dto/create-clinical-record.dto';
import { UpdateClinicalRecordDto } from './dto/update-clinical-record.dto';
import { FilterClinicalRecordsDto } from './dto/filter-clinical-records.dto';
import { JwtAuthGuard } from 'src/core/auth/guards/jwt-auth.guard';
import { PermissionsGuard } from 'src/core/auth/guards/permissions.guard';
import { Permissions } from 'src/core/decorators/permissions.decorator';
import { Permission } from 'src/core/enums/permissions.enum';

@Controller('clinical-records')
@UseGuards(JwtAuthGuard, PermissionsGuard)
export class ClinicalRecordsController {
  constructor(
    private readonly clinicalRecordsService: ClinicalRecordsService,
  ) {}

  @Post()
  @Permissions(Permission.CREATE_PATIENT_CLINICAL_RECORDS)
  create(@Body() createDto: CreateClinicalRecordDto, @Request() req) {
    return this.clinicalRecordsService.create(createDto, req.user);
  }

  @Get()
  @Permissions(Permission.VIEW_PATIENT_CLINICAL_RECORDS)
  findAll(@Query() filters: FilterClinicalRecordsDto, @Request() req) {
    return this.clinicalRecordsService.findAll(filters, req.user);
  }

  @Get('me')
  @UseGuards(JwtAuthGuard)
  findMyClinicalRecords(@Request() req) {
    return this.clinicalRecordsService.findByCurrentPatient(req.user);
  }

  @Get(':id')
  @Permissions(Permission.VIEW_PATIENT_CLINICAL_RECORDS)
  findOne(@Param('id', ParseIntPipe) id: number, @Request() req) {
    return this.clinicalRecordsService.findOne(id, req.user);
  }

  @Patch(':id')
  @Permissions(Permission.EDIT_PATIENT_CLINICAL_RECORDS)
  update(
    @Param('id', ParseIntPipe) id: number,
    @Body() updateDto: UpdateClinicalRecordDto,
    @Request() req,
  ) {
    return this.clinicalRecordsService.update(id, updateDto, req.user);
  }
}
