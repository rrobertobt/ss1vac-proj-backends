import {
  Controller,
  Post,
  Body,
  UseGuards,
  Patch,
  Param,
  ParseIntPipe,
  Get,
  Query,
} from '@nestjs/common';
import { EmployeesService } from './employees.service';
import { CreateEmployeeDto } from './dto/create-employee.dto';
import { UpdateEmployeeDto } from './dto/update-employee.dto';
import { FilterEmployeesDto } from './dto/filter-employees.dto';
import { JwtAuthGuard } from 'src/core/auth/guards/jwt-auth.guard';
import { PermissionsGuard } from 'src/core/auth/guards/permissions.guard';
import { Permissions } from 'src/core/decorators/permissions.decorator';
import { Permission } from 'src/core/enums/permissions.enum';

@Controller('employees')
@UseGuards(JwtAuthGuard, PermissionsGuard)
export class EmployeesController {
  constructor(private readonly employeesService: EmployeesService) {}

  @Post()
  @Permissions(Permission.CREATE_EMPLOYEES)
  create(@Body() createEmployeeDto: CreateEmployeeDto) {
    return this.employeesService.create(createEmployeeDto);
  }

  @Get()
  @Permissions(Permission.VIEW_EMPLOYEES)
  findAll(@Query() filters: FilterEmployeesDto) {
    return this.employeesService.findAll(filters);
  }

  @Get(':id')
  @Permissions(Permission.VIEW_EMPLOYEES)
  findOne(@Param('id', ParseIntPipe) id: number) {
    return this.employeesService.findOne(id);
  }

  @Patch(':id')
  @Permissions(Permission.EDIT_EMPLOYEES)
  update(
    @Param('id', ParseIntPipe) id: number,
    @Body() updateEmployeeDto: UpdateEmployeeDto,
  ) {
    return this.employeesService.update(id, updateEmployeeDto);
  }
}
