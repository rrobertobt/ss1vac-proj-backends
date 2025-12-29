import {
  Controller,
  Post,
  Get,
  Body,
  Param,
  UseGuards,
  ParseIntPipe,
  Request,
} from '@nestjs/common';
import { ConfidentialNotesService } from './confidential-notes.service';
import { CreateConfidentialNoteDto } from './dto/create-confidential-note.dto';
import { JwtAuthGuard } from 'src/core/auth/guards/jwt-auth.guard';
import { PermissionsGuard } from 'src/core/auth/guards/permissions.guard';
import { Permissions } from 'src/core/decorators/permissions.decorator';
import { Permission } from 'src/core/enums/permissions.enum';

@Controller('clinical-records')
@UseGuards(JwtAuthGuard, PermissionsGuard)
export class ConfidentialNotesController {
  constructor(
    private readonly confidentialNotesService: ConfidentialNotesService,
  ) {}

  @Post(':id/confidential-notes')
  @Permissions(Permission.CREATE_CONFIDENTIAL_NOTES)
  create(
    @Param('id', ParseIntPipe) clinicalRecordId: number,
    @Body() createDto: CreateConfidentialNoteDto,
    @Request() req,
  ) {
    return this.confidentialNotesService.create(
      clinicalRecordId,
      createDto,
      req.user,
    );
  }

  @Get(':id/confidential-notes')
  @Permissions(Permission.VIEW_CONFIDENTIAL_NOTES)
  findByClinicalRecord(@Param('id', ParseIntPipe) clinicalRecordId: number) {
    return this.confidentialNotesService.findByClinicalRecord(clinicalRecordId);
  }
}
