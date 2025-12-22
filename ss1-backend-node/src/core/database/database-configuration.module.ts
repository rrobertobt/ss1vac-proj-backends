import { Global, Module } from '@nestjs/common';
import * as Knex from 'knex';
import { Model } from 'objection';
import * as dotenv from 'dotenv';
import { UserModel } from 'src/modules/users/entities/user.entity';

dotenv.config();

// Insert database models here
const models = [UserModel];

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
