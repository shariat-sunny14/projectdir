export type Role = "SUPER_ADMIN" | "ADMIN" | "TRANSPORT_MANAGER" | "EMPLOYEE" | "DRIVER";
export type UserStatus = "PENDING" | "ACTIVE" | "REJECTED" | "SUSPENDED";

export interface User {
  id: string; // USR-001
  fullName: string;
  email: string;
  phone: string;
  employeeId?: string;
  departmentId?: string;
  designation?: string;
  passwordHash: string;
  role: Role;
  status: UserStatus;
  profileImage?: string;
  address?: string;
  googleId?: string;
  rejectionReason?: string;
  createdAt: string;
  updatedAt: string;
}

export type DepartmentStatus = "ACTIVE" | "INACTIVE";

export interface Department {
  id: string; // DEP-001
  code: string;
  name: string;
  manager?: string;
  description?: string;
  status: DepartmentStatus;
  createdAt: string;
  updatedAt: string;
}

export type VehicleType = "Sedan" | "SUV" | "Microbus" | "Bus" | "Pickup" | "Van" | "Other";
export type FuelType = "Petrol" | "Octane" | "Diesel" | "CNG" | "Hybrid" | "Electric";
export type VehicleStatus = "AVAILABLE" | "BOOKED" | "ON_TRIP" | "MAINTENANCE" | "INACTIVE";
export const BLOCKING_BOOKING_STATUSES = ["PENDING", "APPROVED", "ON_TRIP"] as const;

export interface Vehicle {
  id: string; // VEH-001
  registrationNumber: string;
  vehicleName: string;
  brand?: string;
  model?: string;
  modelYear?: number;
  vehicleType: VehicleType;
  color?: string;
  seatingCapacity?: number;
  fuelType: FuelType;
  currentKm: number;
  purchaseDate?: string;
  purchasePrice?: number;
  assignedDepartmentId?: string;
  insuranceExpiry?: string;
  fitnessExpiry?: string;
  taxTokenExpiry?: string;
  status: VehicleStatus;
  notes?: string;
  currentLat?: number;
  currentLng?: number;
  locationUpdatedAt?: string;
  createdAt: string;
  updatedAt: string;
}

export type DriverStatus = "AVAILABLE" | "BOOKED" | "ON_TRIP" | "OFF_DUTY" | "INACTIVE";

export interface Driver {
  id: string; // DRV-001
  userId?: string; // linked login account, if any
  driverName: string;
  phone: string;
  email?: string;
  licenseNumber: string;
  licenseType?: string;
  licenseExpiryDate: string;
  joiningDate?: string;
  assignedVehicleId?: string;
  emergencyContact?: string;
  address?: string;
  status: DriverStatus;
  createdAt: string;
  updatedAt: string;
}

export type BookingStatus = "PENDING" | "APPROVED" | "REJECTED" | "CANCELLED" | "ON_TRIP" | "COMPLETED";

/** A geocoded point selected from the location-search autocomplete (Uber-style pickup/destination picker). */
export interface GeoLocation {
  name: string;
  address: string;
  lat: number;
  lng: number;
}

export interface Booking {
  id: string; // BK-00125
  employeeId: string;
  departmentId?: string;
  startDateTime: string;
  endDateTime: string;
  pickupLocation: string;
  destinationLocation: string;
  pickupLocationDetails?: GeoLocation;
  destinationLocationDetails?: GeoLocation;
  purpose: string;
  passengerCount?: number;
  remarks?: string;
  requestedVehicleId: string;
  assignedVehicleId: string | null;
  assignedDriverId: string | null;
  status: BookingStatus;
  rejectionReason?: string;
  createdAt: string;
  updatedAt: string;
}

export type MaintenanceStatus = "OPEN" | "COMPLETED";

export type ServiceType =
  | "General Service"
  | "Engine Oil"
  | "Brake"
  | "Battery"
  | "AC"
  | "Tyre"
  | "Engine"
  | "Electrical"
  | "Repair"
  | "Other";

export interface MaintenanceRecord {
  id: string; // SRV-00125
  vehicleId: string;
  serviceDate: string;
  serviceType: ServiceType;
  currentKm?: number;
  workshop?: string;
  mechanic?: string;
  description?: string;
  partsCost: number;
  labourCost: number;
  otherCost: number;
  totalCost: number;
  nextServiceDate?: string;
  nextServiceKm?: number;
  invoiceNumber?: string;
  remarks?: string;
  status: MaintenanceStatus;
  submittedByUserId?: string;
  approvalStatus: "PENDING" | "APPROVED" | "REJECTED";
  approvalRejectionReason?: string;
  documentPath?: string;
  createdAt: string;
  updatedAt: string;
}

export type ExpenseCategory =
  | "FUEL"
  | "TOLL"
  | "TIP"
  | "PARKING"
  | "REPAIR"
  | "SERVICE"
  | "INSURANCE"
  | "TAX"
  | "OTHER";

export type PaymentMethod = "CASH" | "BANK" | "DEBIT_CARD" | "CREDIT_CARD" | "BKASH" | "NAGAD" | "OTHER";

export interface Expense {
  id: string; // EXP-00125
  vehicleId: string;
  bookingId?: string;
  expenseDate: string;
  category: ExpenseCategory;
  location?: string;
  amount: number;
  paymentMethod: PaymentMethod;
  description?: string;
  createdByUserId: string;
  approvalStatus: "PENDING" | "APPROVED" | "REJECTED";
  approvalRejectionReason?: string;
  documentPath?: string;
  createdAt: string;
  updatedAt: string;
}

export type AuditAction =
  | "LOGIN"
  | "LOGOUT"
  | "CREATE"
  | "UPDATE"
  | "DELETE"
  | "APPROVE"
  | "REJECT"
  | "ASSIGN"
  | "VEHICLE_CHANGE"
  | "START_TRIP"
  | "COMPLETE_TRIP"
  | "CANCEL";

/** OTP-based password reset record (Feature #12). One row per requested code;
 * superseded codes are marked used so only the latest one is ever valid. */
export interface PasswordResetOtp {
  id: string;
  userId: string;
  email: string;
  otpHash: string;
  expiresAt: string;
  used: boolean;
  verified: boolean;
  attempts: number;
  maxAttempts: number;
  lastSentAt: string;
  createdAt: string;
  updatedAt: string;
}

export interface AuditLog {
  id: string; // AUD-00125
  userId: string;
  module: string;
  action: AuditAction | string;
  recordId: string;
  description?: string;
  ipAddress?: string;
  createdAt: string;
  updatedAt: string;
}

export type TripStatus = "RUNNING" | "COMPLETED";

export interface Trip {
  id: string; // TRP-00125
  bookingId: string;
  vehicleId: string;
  driverId: string | null;
  actualStart: string;
  startingKm: number;
  startLocation?: string;
  startLocationDetails?: GeoLocation;
  startRemarks?: string;
  actualEnd?: string;
  endingKm?: number;
  endLocation?: string;
  endLocationDetails?: GeoLocation;
  endRemarks?: string;
  totalKm?: number;
  status: TripStatus;
  createdAt: string;
  updatedAt: string;
}

/** One GPS ping recorded while a trip is RUNNING (Feature #14 live tracking history). */
export interface VehicleLocationPing {
  id: string;
  tripId: string;
  vehicleId: string;
  driverId: string | null;
  bookingId: string;
  lat: number;
  lng: number;
  recordedAt: string;
  createdAt: string;
  updatedAt: string;
}

export interface BookingVehicleHistory {
  id: string;
  bookingId: string;
  oldVehicleId: string | null;
  newVehicleId: string;
  changedBy: string;
  reason: string;
  changedAt: string;
  createdAt: string;
  updatedAt: string;
}

export type NotificationType =
  | "USER_APPROVAL"
  | "BOOKING_CREATED"
  | "BOOKING_APPROVED"
  | "BOOKING_REJECTED"
  | "VEHICLE_CHANGED"
  | "DRIVER_ASSIGNED"
  | "TRIP_COMPLETED"
  | "MAINTENANCE"
  | "SYSTEM";

export interface Notification {
  id: string; // NOT-00125
  userId: string;
  title: string;
  message: string;
  type: NotificationType;
  relatedId?: string;
  isRead: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface EmailLog {
  id: string; // EML-00125
  to: string;
  event: string;
  subject: string;
  body: string;
  status: "SENT" | "FAILED";
  errorMessage?: string;
  createdAt: string;
  updatedAt: string;
}
