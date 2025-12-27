import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';
import { ValidationPipe } from '@nestjs/common';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  app.enableCors();

  // Habilitar validación global
  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true, // Remueve propiedades no definidas en el DTO
      forbidNonWhitelisted: true, // Lanza error si hay propiedades extra
      transform: true, // Transforma los payloads a las instancias del DTO
      transformOptions: {
        enableImplicitConversion: true, // Convierte tipos automáticamente
      },
    }),
  );

  await app.listen(process.env.PORT ?? 3001);
}
bootstrap();
