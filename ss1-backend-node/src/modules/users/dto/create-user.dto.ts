import {
  IsEmail,
  IsNotEmpty,
  IsString,
  IsInt,
  IsBoolean,
  IsOptional,
  MinLength,
} from 'class-validator';

export class CreateUserDto {
  @IsEmail()
  @IsNotEmpty()
  email: string;

  @IsString()
  @IsOptional()
  username?: string;

  @IsString()
  @MinLength(8)
  @IsNotEmpty()
  password: string;

  @IsInt()
  @IsNotEmpty()
  role_id: number;

  @IsBoolean()
  @IsOptional()
  is_active?: boolean;
}
