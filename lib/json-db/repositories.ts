import { createRepository } from "./repository";
import type {
  User,
  Department,
  Vehicle,
  Driver,
  Booking,
  AuditLog,
  EmailLog,
  MaintenanceRecord,
  Expense,
  Trip,
  Notification,
  BookingVehicleHistory,
  PasswordResetOtp,
  VehicleLocationPing,
} from "@/lib/types";

export const usersRepo = createRepository<User>("users");
export const departmentsRepo = createRepository<Department>("departments");
export const vehiclesRepo = createRepository<Vehicle>("vehicles");
export const driversRepo = createRepository<Driver>("drivers");
export const bookingsRepo = createRepository<Booking>("bookings");
export const auditLogsRepo = createRepository<AuditLog>("audit_logs");
export const emailLogsRepo = createRepository<EmailLog>("email_logs");
export const maintenanceRepo = createRepository<MaintenanceRecord>("maintenance");
export const expensesRepo = createRepository<Expense>("expenses");
export const tripsRepo = createRepository<Trip>("trips");
export const notificationsRepo = createRepository<Notification>("notifications");
export const bookingVehicleHistoryRepo = createRepository<BookingVehicleHistory>("booking_vehicle_history");
export const passwordResetOtpsRepo = createRepository<PasswordResetOtp>("password_reset_otps");
export const vehicleLocationsRepo = createRepository<VehicleLocationPing>("vehicle_locations");
