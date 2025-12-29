import { Model, RelationMappings, RelationMappingsThunk } from 'objection';
import { InvoiceModel } from './invoice.entity';

export class PaymentMethodModel extends Model {
  static tableName = 'payment_methods';

  id: number;
  name: string;
  created_at: Date;
}

export class PaymentModel extends Model {
  static tableName = 'payments';

  id: number;
  invoice_id: number;
  payment_method_id: number | null;
  amount: number;
  paid_at: Date;
  reference: string | null;
  created_at: Date;

  // Relaciones
  invoice?: InvoiceModel;
  payment_method?: PaymentMethodModel;

  static get relationMappings(): RelationMappings | RelationMappingsThunk {
    return {
      invoice: {
        relation: Model.BelongsToOneRelation,
        modelClass: InvoiceModel,
        join: {
          from: 'payments.invoice_id',
          to: 'invoices.id',
        },
      },
      payment_method: {
        relation: Model.BelongsToOneRelation,
        modelClass: PaymentMethodModel,
        join: {
          from: 'payments.payment_method_id',
          to: 'payment_methods.id',
        },
      },
    };
  }
}
