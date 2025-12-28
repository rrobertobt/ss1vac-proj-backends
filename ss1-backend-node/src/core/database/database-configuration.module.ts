import { Global, Module } from '@nestjs/common';
import * as Knex from 'knex';
import { Model } from 'objection';
import * as dotenv from 'dotenv';
import { UserModel } from 'src/modules/users/entities/user.entity';
import { EmployeeModel } from 'src/modules/employees/entities/employee.entity';
import { PatientModel } from 'src/modules/patients/entities/patient.entity';
import { RoleModel } from 'src/modules/roles/entities/role.entity';
import { AreaModel } from 'src/modules/areas/entities/area.entity';
import { SpecialtyModel } from 'src/modules/specialties/entities/specialty.entity';
import { EmployeeSpecialtyModel } from 'src/modules/specialties/entities/employee-specialty.entity';
import { ServiceModel } from 'src/modules/services/entities/service.entity';
import { EmployeeAvailabilityModel } from 'src/modules/employees/entities/employee-availability.entity';

dotenv.config();

// Insert database models here
const models = [
  UserModel,
  EmployeeModel,
  PatientModel,
  RoleModel,
  AreaModel,
  SpecialtyModel,
  EmployeeSpecialtyModel,
  ServiceModel,
  EmployeeAvailabilityModel,
];

const modelProviders = models.map((model) => {
  return {
    provide: model.name,
    useValue: model,
  };
});

const providers = [
  ...modelProviders,
  {
    provide: 'KnexConnection',
    useFactory: () => {
      const knex = Knex.knex({
        client: process.env.DB_PROVIDER,
        connection: {
          host: process.env.DB_HOST,
          port: parseInt(process.env.DB_PORT ?? '5432', 10) || 5432,
          user: process.env.DB_USER,
          password: process.env.DB_PASS,
          database: process.env.DB_NAME,
          debug: process.env.NODE_ENV === 'development',
        },
      });
      Model.knex(knex);
      return knex;
    },
  },
];

@Global()
@Module({
  providers: [...providers],
  exports: [...providers],
})
export class DatabaseConfigurationModule {}
