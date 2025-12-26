import {
  ConflictException,
  Inject,
  Injectable,
  NotFoundException,
} from '@nestjs/common';
import { CreateUserDto } from './dto/create-user.dto';
import { UpdateUserDto } from './dto/update-user.dto';
import { UpdateUserStatusDto } from './dto/update-user-status.dto';
import { FilterUsersDto } from './dto/filter-users.dto';
import { UserModel } from './entities/user.entity';
import { Transaction, type ModelClass } from 'objection';
import * as bcrypt from 'bcrypt';

@Injectable()
export class UsersService {
  constructor(
    @Inject(UserModel.name) private userModel: ModelClass<UserModel>,
  ) {}

  async findByEmailOrUsername(emailOrUsername: string, trx?: Transaction) {
    const user = await this.userModel
      .query(trx)
      .where('email', emailOrUsername)
      .orWhere('username', emailOrUsername)
      .withGraphFetched('[role.permissions, employee, patient]')
      .first();
    return user;
  }

  async findById(
    id: number,
    trx?: Transaction,
  ): Promise<UserModel | undefined> {
    const query = await this.userModel
      .query(trx)
      .findById(id)
      .withGraphFetched('[role.permissions, employee, patient]');
    delete query?.password_hash;
    return query;
  }

  async findAll(filters: FilterUsersDto) {
    const { page = 1, limit = 10, role_id, is_active, search } = filters;
    const offset = (page - 1) * limit;

    let query = this.userModel
      .query()
      .withGraphFetched('[role, employee, patient]')
      .orderBy('created_at', 'desc');

    // Filtros
    if (role_id !== undefined) {
      query = query.where('role_id', role_id);
    }

    if (is_active !== undefined) {
      query = query.where('is_active', is_active);
    }

    if (search) {
      query = query.where((builder) => {
        builder
          .where('email', 'ilike', `%${search}%`)
          .orWhere('username', 'ilike', `%${search}%`);
      });
    }

    const [users, total] = await Promise.all([
      query.limit(limit).offset(offset),
      query.resultSize(),
    ]);

    // Remover password_hash de todos los usuarios
    users.forEach((user) => delete user.password_hash);

    return {
      data: users,
      meta: {
        total,
        page,
        limit,
        totalPages: Math.ceil(total / limit),
      },
    };
  }

  async findOne(id: number) {
    const user = await this.userModel
      .query()
      .findById(id)
      .withGraphFetched('[role.permissions, employee, patient]');

    if (!user) {
      throw new NotFoundException(`Usuario con ID ${id} no encontrado`);
    }

    delete user.password_hash;
    return user;
  }

  async create(createUserDto: CreateUserDto) {
    // Verificar si el email ya existe
    const existingUser = await this.userModel
      .query()
      .where('email', createUserDto.email)
      .first();

    if (existingUser) {
      throw new ConflictException('El email ya está registrado');
    }

    // Verificar si el username ya existe (si se proporcionó)
    if (createUserDto.username) {
      const existingUsername = await this.userModel
        .query()
        .where('username', createUserDto.username)
        .first();

      if (existingUsername) {
        throw new ConflictException('El username ya está registrado');
      }
    }

    // Hashear la contraseña
    const hashedPassword = await bcrypt.hash(createUserDto.password, 10);

    // Crear usuario
    const user = await this.userModel.query().insert({
      email: createUserDto.email,
      username: createUserDto.username,
      password_hash: hashedPassword,
      role_id: createUserDto.role_id,
      is_active: createUserDto.is_active ?? true,
    });

    // Obtener usuario completo con relaciones
    const createdUser = await this.findById(user.id);
    return createdUser;
  }

  async update(id: number, updateUserDto: UpdateUserDto) {
    const user = await this.userModel.query().findById(id);

    if (!user) {
      throw new NotFoundException(`Usuario con ID ${id} no encontrado`);
    }

    // Verificar si el nuevo email ya existe
    if (updateUserDto.email && updateUserDto.email !== user.email) {
      const existingEmail = await this.userModel
        .query()
        .where('email', updateUserDto.email)
        .whereNot('id', id)
        .first();

      if (existingEmail) {
        throw new ConflictException('El email ya está registrado');
      }
    }

    // Verificar si el nuevo username ya existe
    if (updateUserDto.username && updateUserDto.username !== user.username) {
      const existingUsername = await this.userModel
        .query()
        .where('username', updateUserDto.username)
        .whereNot('id', id)
        .first();

      if (existingUsername) {
        throw new ConflictException('El username ya está registrado');
      }
    }

    // Actualizar usuario
    await this.userModel.query().patchAndFetchById(id, updateUserDto);

    // Retornar usuario actualizado con relaciones
    return this.findById(id);
  }

  async updateStatus(id: number, updateStatusDto: UpdateUserStatusDto) {
    const user = await this.userModel.query().findById(id);

    if (!user) {
      throw new NotFoundException(`Usuario con ID ${id} no encontrado`);
    }

    await this.userModel.query().patchAndFetchById(id, {
      is_active: updateStatusDto.is_active,
    });

    return this.findById(id);
  }

  remove(id: number) {
    return `This action removes a #${id} user`;
  }
}
