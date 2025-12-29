import { IsNotEmpty, IsString } from 'class-validator';

export class CreateConfidentialNoteDto {
  @IsString()
  @IsNotEmpty()
  content: string;
}
