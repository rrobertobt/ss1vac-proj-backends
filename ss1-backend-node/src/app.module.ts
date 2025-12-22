import { Module } from '@nestjs/common';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { DatabaseConfigurationModule } from './core/database/database-configuration.module';
import { DatabaseTransactionModule } from './core/database/transaction/database-transaction.module';

@Module({
  imports: [DatabaseConfigurationModule, DatabaseTransactionModule],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}
