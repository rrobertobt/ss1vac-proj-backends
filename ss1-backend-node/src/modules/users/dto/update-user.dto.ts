import {
  IsEmail,
  IsString,
  IsInt,
  IsBoolean,
  IsOptional,
} from 'class-validator';

export class UpdateUserDto {
  @IsEmail()
  @IsOptional()
  email?: string;

  @IsString()
  @IsOptional()
  username?: string;

  @IsInt()
  @IsOptional()
  role_id?: number;

  @IsBoolean()
  @IsOptional()
  is_active?: boolean;

  @IsOptional()
  last_login_at?: Date | null;
}
