/* eslint-disable @typescript-eslint/no-unsafe-member-access */
/* eslint-disable @typescript-eslint/no-unsafe-argument */
import {
  BadRequestException,
  HttpException,
  Injectable,
  InternalServerErrorException,
  Logger,
  UnprocessableEntityException,
} from '@nestjs/common';
import { Model, Transaction } from 'objection';
import { IGeneralError } from 'src/core/interfaces/general-error.interface';

@Injectable()
export class DatabaseTransactionService {
  async databaseTransaction<T>(
    executeFunction: (t: Transaction) => Promise<T>,
    logger?: Logger,
  ): Promise<T> {
    const transaction: Transaction = await Model.startTransaction();
    try {
      const res: T = await executeFunction(transaction);
      await transaction.commit();
      return res;
    } catch (err) {
      if (logger !== undefined) {
        if (err instanceof HttpException) {
          logger.error(err.message, err.stack, err.getResponse());
        } else {
          logger.error(err);
        }
      }
      await transaction.rollback();
      if (!this.isGeneralErrorObject(err)) {
        if (err['name'] && err['name'] === 'UniqueViolationError') {
          let errors: object[] | string;
          let badRequest = true;
          if (err['columns']) {
            errors = (err['columns'] as string[]).map((col: string) => {
              return {
                [col]: ['A record with the specified value already exists'],
              };
            });
          } else {
            badRequest = false;
            errors = 'Duplicate record';
          }
          const error: IGeneralError = {
            statusCode: badRequest ? 400 : 422,
            message: errors,
            error: badRequest ? 'Bad request' : 'Unprocessable Entity',
          };
          if (badRequest) {
            throw new BadRequestException(error);
          } else {
            throw new UnprocessableEntityException(error);
          }
        } else {
          const error: IGeneralError = {
            statusCode: 500,
            message: 'Internal server error',
            error: 'Internal server error',
          };
          throw new InternalServerErrorException(error);
        }
      }
      throw new HttpException(err['response'], err['status']);
    }
  }

  private isGeneralErrorObject(obj: any): boolean {
    if (obj['status'] === undefined || obj['response'] === undefined) {
      return false;
    }
    if (typeof obj['response'] !== 'object') {
      return false;
    }
    return (
      'statusCode' in obj['response'] &&
      'message' in obj['response'] &&
      'error' in obj['response']
    );
  }
}
