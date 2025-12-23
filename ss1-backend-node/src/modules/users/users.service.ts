import { Inject, Injectable } from '@nestjs/common';
import { CreateUserDto } from './dto/create-user.dto';
import { UserModel } from './entities/user.entity';
import { Transaction, type ModelClass } from 'objection';

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
      .withGraphFetched('role')
      .first();
    console.log('findByEmailOrUsername found user:', user);
    return user;
  }

  async findById(
    id: number,
    trx?: Transaction,
  ): Promise<UserModel | undefined> {
    const query = await this.userModel
      .query(trx)
      .findById(id)
      .withGraphFetched('role');
    delete query?.password_hash;
    return query;
  }

  async update(id: number, patch: Record<string, any>) {
    return this.userModel.query().patchAndFetchById(id, patch);
  }

  create(createUserDto: CreateUserDto) {
    return 'This action adds a new user';
  }

  findAll() {
    return `This action returns all users`;
  }

  findOne(id: number) {
    return `This action returns a #${id} user`;
  }

  remove(id: number) {
    return `This action removes a #${id} user`;
  }
}
