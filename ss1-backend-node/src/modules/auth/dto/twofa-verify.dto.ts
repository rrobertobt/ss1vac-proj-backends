import { IsNotEmpty, IsString, Length } from 'class-validator';

export class TwoFaVerifyDto {
  @IsString()
  @IsNotEmpty()
  challengeId: string;

  @IsString()
  @Length(6, 6)
  code: string;
}
