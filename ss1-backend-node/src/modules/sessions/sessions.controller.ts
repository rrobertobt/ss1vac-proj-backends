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
import { SessionsService } from './sessions.service';
import { CreateSessionDto } from './dto/create-session.dto';
import { UpdateSessionDto } from './dto/update-session.dto';
import { JwtAuthGuard } from 'src/core/auth/guards/jwt-auth.guard';
import { PermissionsGuard } from 'src/core/auth/guards/permissions.guard';
import { Permissions } from 'src/core/decorators/permissions.decorator';
import { Permission } from 'src/core/enums/permissions.enum';

@Controller()
@UseGuards(JwtAuthGuard, PermissionsGuard)
export class SessionsController {
  constructor(private readonly sessionsService: SessionsService) {}

  @Post('clinical-records/:id/sessions')
  @Permissions(Permission.CREATE_SESSIONS)
  create(
    @Param('id', ParseIntPipe) clinicalRecordId: number,
    @Body() createDto: CreateSessionDto,
    @Request() req,
  ) {
    return this.sessionsService.create(clinicalRecordId, createDto, req.user);
  }

  @Get('clinical-records/:id/sessions')
  @Permissions(Permission.VIEW_SESSIONS)
  findByClinicalRecord(@Param('id', ParseIntPipe) clinicalRecordId: number) {
    return this.sessionsService.findByClinicalRecord(clinicalRecordId);
  }

  @Patch('clinical-sessions/:sessionId')
  @Permissions(Permission.EDIT_SESSIONS)
  update(
    @Param('sessionId', ParseIntPipe) sessionId: number,
    @Body() updateDto: UpdateSessionDto,
  ) {
    return this.sessionsService.update(sessionId, updateDto);
  }
}
