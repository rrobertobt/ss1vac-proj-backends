import { Model } from 'objection';

export class UserModel extends Model {
  static tableName = 'users';

  id: number;
  email: string;
  username: string;
  password_hash?: string;
  role_id: number;
  is_active: boolean;
  last_login_at: Date | null;
  two_fa_enabled: boolean;
  two_fa_secret: string | null;
  two_fa_expires_at: Date | null;
  two_fa_attempts: number | null;
  password_reset_token: string | null;
  password_reset_expires: Date | null;
  created_at: Date;
  updated_at: Date;
}
