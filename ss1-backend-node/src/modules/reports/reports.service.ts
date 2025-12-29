import { Injectable, Inject } from '@nestjs/common';
import { type ModelClass } from 'objection';
import type { InvoiceModel } from './entities/invoice.entity';
import type { PaymentModel } from './entities/payment.entity';
import type { PayrollRecordModel } from './entities/payroll-record.entity';
import type { AppointmentModel } from '../appointments/entities/appointment.entity';
import {
  RevenueReportDto,
  PayrollReportDto,
  SalesHistoryDto,
  PatientsPerSpecialtyDto,
} from './dto/reports.dto';

@Injectable()
export class ReportsService {
  constructor(
    @Inject('InvoiceModel')
    private invoiceModel: ModelClass<InvoiceModel>,
    @Inject('PaymentModel')
    private paymentModel: ModelClass<PaymentModel>,
    @Inject('PayrollRecordModel')
    private payrollRecordModel: ModelClass<PayrollRecordModel>,
    @Inject('AppointmentModel')
    private appointmentModel: ModelClass<AppointmentModel>,
  ) {}

  /**
   * Reporte: Ingresos por período
   * Obtiene el total de ingresos basados en facturas y pagos realizados
   */
  async getRevenueReport(dto: RevenueReportDto) {
    const { start_date, end_date, currency = 'GTQ' } = dto;

    // Obtener facturas en el período
    const invoices = await this.invoiceModel
      .query()
      .whereBetween('invoice_date', [start_date, end_date])
      .where('currency', currency)
      .whereIn('status', ['ISSUED', 'PAID'])
      .withGraphFetched('[patient, items.[service, product]]');

    // Obtener pagos realizados en el período
    const payments = await this.paymentModel
      .query()
      .whereBetween('paid_at', [start_date, end_date])
      .withGraphFetched('[invoice.patient, payment_method]')
      .whereExists(
        this.invoiceModel
          .query()
          .whereColumn('invoices.id', 'payments.invoice_id')
          .where('invoices.currency', currency),
      );

    // Calcular totales
    const totalInvoiced = invoices.reduce(
      (sum, inv) => sum + Number(inv.total_amount),
      0,
    );
    const totalPaid = payments.reduce(
      (sum, pay) => sum + Number(pay.amount),
      0,
    );

    // Agrupar por mes
    const byMonth = invoices.reduce(
      (acc, invoice) => {
        const month = new Date(invoice.invoice_date).toISOString().slice(0, 7);
        if (!acc[month]) {
          acc[month] = { invoiced: 0, paid: 0, count: 0 };
        }
        acc[month].invoiced += Number(invoice.total_amount);
        acc[month].count += 1;
        return acc;
      },
      {} as Record<string, { invoiced: number; paid: number; count: number }>,
    );

    payments.forEach((payment) => {
      const month = new Date(payment.paid_at).toISOString().slice(0, 7);
      if (byMonth[month]) {
        byMonth[month].paid += Number(payment.amount);
      }
    });

    return {
      period: { start_date, end_date },
      currency,
      summary: {
        total_invoiced: totalInvoiced,
        total_paid: totalPaid,
        pending: totalInvoiced - totalPaid,
        invoices_count: invoices.length,
        payments_count: payments.length,
      },
      by_month: Object.entries(byMonth).map(([month, data]) => ({
        month,
        ...data,
      })),
      invoices: invoices.map((inv) => ({
        id: inv.id,
        invoice_number: inv.invoice_number,
        invoice_date: inv.invoice_date,
        patient: inv.patient
          ? `${inv.patient.first_name} ${inv.patient.last_name}`
          : null,
        total_amount: inv.total_amount,
        status: inv.status,
      })),
      payments: payments.map((pay) => ({
        id: pay.id,
        paid_at: pay.paid_at,
        amount: pay.amount,
        payment_method: pay.payment_method?.name,
        invoice_number: pay.invoice?.invoice_number,
        patient: pay.invoice?.patient
          ? `${pay.invoice.patient.first_name} ${pay.invoice.patient.last_name}`
          : null,
      })),
    };
  }

  /**
   * Reporte: Pagos realizados a empleados
   * Obtiene los pagos de nómina a empleados en un período
   */
  async getPayrollReport(dto: PayrollReportDto) {
    const { start_date, end_date, employee_id } = dto;

    let query = this.payrollRecordModel
      .query()
      .withGraphFetched('[employee.area, period]')
      .whereExists(
        this.payrollRecordModel
          .relatedQuery('period')
          .whereBetween('period_start', [start_date, end_date])
          .orWhereBetween('period_end', [start_date, end_date]),
      );

    if (employee_id) {
      query = query.where('employee_id', employee_id);
    }

    const records = await query;

    // Calcular totales
    const summary = records.reduce(
      (acc, record) => {
        acc.total_base_salary += Number(record.base_salary_amount);
        acc.total_sessions_amount += Number(record.sessions_amount);
        acc.total_bonuses += Number(record.bonuses_amount);
        acc.total_igss_deduction += Number(record.igss_deduction);
        acc.total_other_deductions += Number(record.other_deductions);
        acc.total_paid += Number(record.total_pay);
        acc.total_sessions += record.sessions_count;
        return acc;
      },
      {
        total_base_salary: 0,
        total_sessions_amount: 0,
        total_bonuses: 0,
        total_igss_deduction: 0,
        total_other_deductions: 0,
        total_paid: 0,
        total_sessions: 0,
        employees_count: new Set(records.map((r) => r.employee_id)).size,
      },
    );

    return {
      period: { start_date, end_date },
      summary,
      records: records.map((record) => ({
        id: record.id,
        employee: record.employee
          ? {
              id: record.employee.id,
              name: `${record.employee.first_name} ${record.employee.last_name}`,
              area: record.employee.area?.name ?? null,
            }
          : null,
        period: {
          start: record.period?.period_start,
          end: record.period?.period_end,
          status: record.period?.status,
        },
        base_salary_amount: record.base_salary_amount,
        sessions_count: record.sessions_count,
        sessions_amount: record.sessions_amount,
        bonuses_amount: record.bonuses_amount,
        igss_deduction: record.igss_deduction,
        other_deductions: record.other_deductions,
        total_pay: record.total_pay,
        paid_at: record.paid_at,
      })),
    };
  }

  /**
   * Reporte: Historial de ventas
   * Obtiene el detalle de todas las ventas (facturas con sus items)
   */
  async getSalesHistory(dto: SalesHistoryDto) {
    const { start_date, end_date, patient_id } = dto;

    let query = this.invoiceModel
      .query()
      .whereBetween('invoice_date', [start_date, end_date])
      .withGraphFetched('[patient, created_by, items.[service, product]]')
      .orderBy('invoice_date', 'desc');

    if (patient_id) {
      query = query.where('patient_id', patient_id);
    }

    const invoices = await query;

    // Calcular estadísticas
    const totalSales = invoices.reduce(
      (sum, inv) => sum + Number(inv.total_amount),
      0,
    );

    const itemsStats = invoices.reduce(
      (acc, invoice) => {
        invoice.items?.forEach((item) => {
          if (item.service_id) {
            acc.services_count++;
            acc.services_amount += Number(item.total_amount);
          } else if (item.product_id) {
            acc.products_count++;
            acc.products_amount += Number(item.total_amount);
          }
        });
        return acc;
      },
      {
        services_count: 0,
        services_amount: 0,
        products_count: 0,
        products_amount: 0,
      },
    );

    return {
      period: { start_date, end_date },
      summary: {
        total_sales: totalSales,
        invoices_count: invoices.length,
        ...itemsStats,
      },
      sales: invoices.map((invoice) => ({
        id: invoice.id,
        invoice_number: invoice.invoice_number,
        invoice_date: invoice.invoice_date,
        patient: invoice.patient
          ? {
              id: invoice.patient.id,
              name: `${invoice.patient.first_name} ${invoice.patient.last_name}`,
              email: invoice.patient.email,
            }
          : null,
        created_by: invoice.created_by
          ? `${invoice.created_by.first_name} ${invoice.created_by.last_name}`
          : null,
        status: invoice.status,
        total_amount: invoice.total_amount,
        currency: invoice.currency,
        items: invoice.items?.map((item) => ({
          id: item.id,
          type: item.service_id ? 'service' : 'product',
          name: item.service?.name || item.product?.name || null,
          description: item.description,
          quantity: item.quantity,
          unit_price: item.unit_price,
          total_amount: item.total_amount,
        })),
      })),
    };
  }

  /**
   * Reporte: Pacientes atendidos por especialidad (área)
   * Obtiene estadísticas de pacientes atendidos agrupados por especialidad y área
   */
  async getPatientsPerSpecialty(dto: PatientsPerSpecialtyDto) {
    const { start_date, end_date, specialty_id, area_id } = dto;

    let query = this.appointmentModel
      .query()
      .whereBetween('start_datetime', [start_date, end_date])
      .where('status', 'COMPLETED')
      .withGraphFetched('[patient, professional.area, specialty]');

    if (specialty_id) {
      query = query.where('specialty_id', specialty_id);
    }

    const appointments = await query;

    // Filtrar por área si se especifica
    const filteredAppointments = area_id
      ? appointments.filter(
          (app) =>
            app.professional?.area &&
            (app.professional.area as any).id === area_id,
        )
      : appointments;

    // Agrupar por especialidad
    const bySpecialty = filteredAppointments.reduce(
      (acc, appointment) => {
        const specialtyName = appointment.specialty?.name || 'Sin especialidad';
        const areaName =
          (appointment.professional?.area as any)?.name || 'Sin área';
        const patientId = appointment.patient_id;

        if (!acc[specialtyName]) {
          acc[specialtyName] = {
            specialty: specialtyName,
            area: areaName,
            appointments_count: 0,
            unique_patients: new Set(),
          };
        }

        acc[specialtyName].appointments_count++;
        acc[specialtyName].unique_patients.add(patientId);

        return acc;
      },
      {} as Record<
        string,
        {
          specialty: string;
          area: string;
          appointments_count: number;
          unique_patients: Set<number>;
        }
      >,
    );

    // Convertir a array y calcular promedios
    const specialtyStats = Object.values(bySpecialty).map((stat) => ({
      specialty: stat.specialty,
      area: stat.area,
      appointments_count: stat.appointments_count,
      unique_patients_count: stat.unique_patients.size,
      avg_appointments_per_patient: Number(
        (stat.appointments_count / stat.unique_patients.size).toFixed(2),
      ),
    }));

    const totalUniquePatients = new Set(
      filteredAppointments.map((app) => app.patient_id),
    ).size;

    return {
      period: { start_date, end_date },
      summary: {
        total_appointments: filteredAppointments.length,
        total_unique_patients: totalUniquePatients,
        specialties_count: specialtyStats.length,
      },
      by_specialty: specialtyStats.sort(
        (a, b) => b.appointments_count - a.appointments_count,
      ),
    };
  }
}
