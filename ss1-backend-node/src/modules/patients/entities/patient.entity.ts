import { Model, RelationMappings, RelationMappingsThunk } from 'objection';
import { UserModel } from 'src/modules/users/entities/user.entity';

export class PatientModel extends Model {
  static tableName = 'patients';

  id: number;
  user_id: number | null;
  first_name: string;
  last_name: string;
  dob: Date | null;
  gender: string | null;
  marital_status: string | null;
  occupation: string | null;
  education_level: string | null;
  address: string | null;
  phone: string | null;
  email: string | null;
  emergency_contact_name: string | null;
  emergency_contact_relationship: string | null;
  emergency_contact_phone: string | null;
  status: string;
  created_at: Date;
  updated_at: Date;

  // Relación
  user?: UserModel;

  static get relationMappings(): RelationMappings | RelationMappingsThunk {
    return {
      user: {
        relation: Model.BelongsToOneRelation,
        modelClass: UserModel,
        join: {
          from: 'patients.user_id',
          to: 'users.id',
        },
      },
    };
  }
}
