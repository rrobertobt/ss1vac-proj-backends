import { Model, RelationMappings, RelationMappingsThunk } from 'objection';
import { PatientModel } from '../../patients/entities/patient.entity';
import { EmployeeModel } from '../../employees/entities/employee.entity';

export class InvoiceModel extends Model {
  static tableName = 'invoices';

  id: number;
  invoice_number: string;
  patient_id: number;
  created_by_employee_id: number | null;
  invoice_date: Date;
  due_date: Date | null;
  currency: string;
  total_amount: number;
  status: string; // DRAFT, ISSUED, PAID, CANCELLED
  pdf_path: string | null;
  created_at: Date;
  updated_at: Date;

  // Relaciones
  patient?: PatientModel;
  created_by?: EmployeeModel;
  items?: InvoiceItemModel[];
  payments?: any[];

  static get relationMappings(): RelationMappings | RelationMappingsThunk {
    const {
      InvoiceItemModel: InvoiceItemModelClass,
    } = require('./invoice-item.entity');

    const { PaymentModel: PaymentModelClass } = require('./payment.entity');

    return {
      patient: {
        relation: Model.BelongsToOneRelation,
        modelClass: PatientModel,
        join: {
          from: 'invoices.patient_id',
          to: 'patients.id',
        },
      },
      created_by: {
        relation: Model.BelongsToOneRelation,
        modelClass: EmployeeModel,
        join: {
          from: 'invoices.created_by_employee_id',
          to: 'employees.id',
        },
      },
      items: {
        relation: Model.HasManyRelation,
        modelClass: InvoiceItemModelClass,
        join: {
          from: 'invoices.id',
          to: 'invoice_items.invoice_id',
        },
      },
      payments: {
        relation: Model.HasManyRelation,
        modelClass: PaymentModelClass,
        join: {
          from: 'invoices.id',
          to: 'payments.invoice_id',
        },
      },
    };
  }
}

export class InvoiceItemModel extends Model {
  static tableName = 'invoice_items';

  id: number;
  invoice_id: number;
  service_id: number | null;
  product_id: number | null;
  description: string | null;
  quantity: number;
  unit_price: number;
  total_amount: number;
  created_at: Date;

  // Relaciones
  invoice?: InvoiceModel;
  service?: any;
  product?: any;

  static get relationMappings(): RelationMappings | RelationMappingsThunk {
    const {
      ServiceModel: ServiceModelClass,
    } = require('../../services/entities/service.entity');

    const { ProductModel: ProductModelClass } = require('./product.entity');

    return {
      invoice: {
        relation: Model.BelongsToOneRelation,
        modelClass: InvoiceModel,
        join: {
          from: 'invoice_items.invoice_id',
          to: 'invoices.id',
        },
      },
      service: {
        relation: Model.BelongsToOneRelation,
        modelClass: ServiceModelClass,
        join: {
          from: 'invoice_items.service_id',
          to: 'services.id',
        },
      },
      product: {
        relation: Model.BelongsToOneRelation,
        modelClass: ProductModelClass,
        join: {
          from: 'invoice_items.product_id',
          to: 'products.id',
        },
      },
    };
  }
}
