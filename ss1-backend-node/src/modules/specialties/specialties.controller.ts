import {
  Controller,
  Get,
  Post,
  Body,
  Patch,
  Param,
  Delete,
  ParseIntPipe,
  UseGuards,
} from '@nestjs/common';
import { SpecialtiesService } from './specialties.service';
import { CreateSpecialtyDto } from './dto/create-specialty.dto';
import { UpdateSpecialtyDto } from './dto/update-specialty.dto';
import { JwtAuthGuard } from 'src/core/auth/guards/jwt-auth.guard';
import { PermissionsGuard } from 'src/core/auth/guards/permissions.guard';
import { Permissions } from 'src/core/decorators/permissions.decorator';
import { Permission } from 'src/core/enums/permissions.enum';

@Controller('specialties')
export class SpecialtiesController {
  constructor(private readonly specialtiesService: SpecialtiesService) {}

  @Post()
  @UseGuards(JwtAuthGuard, PermissionsGuard)
  @Permissions(Permission.MANAGE_SPECIALTIES)
  create(@Body() createSpecialtyDto: CreateSpecialtyDto) {
    return this.specialtiesService.create(createSpecialtyDto);
  }

  @Get()
  findAll() {
    return this.specialtiesService.findAll();
  }

  @Get(':id')
  findOne(@Param('id', ParseIntPipe) id: number) {
    return this.specialtiesService.findOne(id);
  }

  @Patch(':id')
  @UseGuards(JwtAuthGuard, PermissionsGuard)
  @Permissions(Permission.MANAGE_SPECIALTIES)
  update(
    @Param('id', ParseIntPipe) id: number,
    @Body() updateSpecialtyDto: UpdateSpecialtyDto,
  ) {
    return this.specialtiesService.update(id, updateSpecialtyDto);
  }

  @Delete(':id')
  @UseGuards(JwtAuthGuard, PermissionsGuard)
  @Permissions(Permission.MANAGE_SPECIALTIES)
  remove(@Param('id', ParseIntPipe) id: number) {
    return this.specialtiesService.remove(id);
  }
}
