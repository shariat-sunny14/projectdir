import { z } from "zod";

export const departmentSchema = z.object({
  code: z.string().min(1, "Department code is required"),
  name: z.string().min(1, "Department name is required"),
  manager: z.string().optional(),
  description: z.string().optional(),
  status: z.enum(["ACTIVE", "INACTIVE"]).default("ACTIVE"),
});

export const vehicleSchema = z.object({
  registrationNumber: z.string().min(1, "Registration number is required"),
  vehicleName: z.string().min(1, "Vehicle name is required"),
  brand: z.string().optional(),
  model: z.string().optional(),
  modelYear: z.coerce.number().optional(),
  vehicleType: z.enum(["Sedan", "SUV", "Microbus", "Bus", "Pickup", "Van", "Other"]),
  color: z.string().optional(),
  seatingCapacity: z.coerce.number().optional(),
  fuelType: z.enum(["Petrol", "Octane", "Diesel", "CNG", "Hybrid", "Electric"]),
  currentKm: z.coerce.number().default(0),
  purchaseDate: z.string().optional(),
  purchasePrice: z.coerce.number().optional(),
  assignedDepartmentId: z.string().optional(),
  insuranceExpiry: z.string().optional(),
  fitnessExpiry: z.string().optional(),
  taxTokenExpiry: z.string().optional(),
  status: z.enum(["AVAILABLE", "BOOKED", "ON_TRIP", "MAINTENANCE", "INACTIVE"]).default("AVAILABLE"),
  notes: z.string().optional(),
});

export const driverSchema = z.object({
  driverName: z.string().min(1, "Driver name is required"),
  phone: z.string().min(1, "Phone is required"),
  email: z.string().email().optional().or(z.literal("")),
  licenseNumber: z.string().min(1, "License number is required"),
  licenseType: z.string().optional(),
  licenseExpiryDate: z.string().min(1, "License expiry date is required"),
  joiningDate: z.string().optional(),
  assignedVehicleId: z.string().optional(),
  emergencyContact: z.string().optional(),
  address: z.string().optional(),
  status: z.enum(["AVAILABLE", "ON_TRIP", "OFF_DUTY", "INACTIVE"]).default("AVAILABLE"),
});

export const bookingStep1Schema = z
  .object({
    startDate: z.string().min(1),
    startTime: z.string().min(1),
    endDate: z.string().min(1),
    endTime: z.string().min(1),
    pickupLocation: z.string().min(1, "Pickup location is required"),
    destinationLocation: z.string().min(1, "Destination is required"),
    purpose: z.string().min(1, "Purpose is required"),
    passengerCount: z.coerce.number().optional(),
    remarks: z.string().optional(),
  })
  .refine(
    (d) => new Date(`${d.startDate}T${d.startTime}`) < new Date(`${d.endDate}T${d.endTime}`),
    { message: "End time must be after start time", path: ["endTime"] }
  );
