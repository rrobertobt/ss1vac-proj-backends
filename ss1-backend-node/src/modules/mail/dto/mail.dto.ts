import {
  IsArray,
  IsEmail,
  IsNotEmpty,
  IsOptional,
  MaxLength,
} from 'class-validator';

export class MailDto {
  @IsNotEmpty()
  @IsEmail()
  to: string[] | string;

  @IsNotEmpty()
  @MaxLength(255)
  subject: string;

  // @IsNotEmpty()
  @IsOptional()
  text: string;

  // @IsNotEmpty()
  @IsOptional()
  category?: string;
}
