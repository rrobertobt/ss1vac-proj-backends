import { Module } from '@nestjs/common';
import { ConfidentialNotesService } from './confidential-notes.service';
import { ConfidentialNotesController } from './confidential-notes.controller';

@Module({
  controllers: [ConfidentialNotesController],
  providers: [ConfidentialNotesService],
  exports: [ConfidentialNotesService],
})
export class ConfidentialNotesModule {}
