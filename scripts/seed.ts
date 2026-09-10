/**
 * Seed script — creates demo accounts, departments, vehicles and drivers so
 * you can exercise the full workflow immediately after setup.
 *
 * Run with: npm run seed
 */
import fs from "fs/promises";
import path from "path";
import bcrypt from "bcryptjs";

const DATA_DIR = path.join(process.cwd(), "data");

async function readJson(name: string) {
  const p = path.join(DATA_DIR, `${name}.json`);
  const raw = await fs.readFile(p, "utf-8").catch(() => "[]");
  return JSON.parse(raw);
}

async function writeJson(name: string, data: unknown) {
  const p = path.join(DATA_DIR, `${name}.json`);
  await fs.writeFile(p, JSON.stringify(data, null, 2), "utf-8");
}

async function nextId(prefix: string, pad: number) {
  const countersPath = path.join(DATA_DIR, "counters.json");
  const counters = JSON.parse(await fs.readFile(countersPath, "utf-8").catch(() => "{}"));
  const next = (counters[prefix] ?? 0) + 1;
  counters[prefix] = next;
  await fs.writeFile(countersPath, JSON.stringify(counters, null, 2), "utf-8");
  return `${prefix}-${String(next).padStart(pad, "0")}`;
}

const now = () => new Date().toISOString();

async function ensureDepartment(departments: any[], code: string, name: string) {
  const existing = departments.find((d) => d.code === code);
  if (existing) return existing;
  const id = await nextId("DEP", 3);
  const dep = { id, code, name, manager: "", description: "", status: "ACTIVE", createdAt: now(), updatedAt: now() };
  departments.push(dep);
  return dep;
}

async function ensureUser(
  users: any[],
  opts: { fullName: string; email: string; phone: string; role: string; departmentId?: string; designation?: string }
) {
  const existing = users.find((u) => u.email === opts.email);
  if (existing) return existing;
  const id = await nextId("USR", 3);
  const passwordHash = await bcrypt.hash("Passw0rd!", 10);
  const user = {
    id,
    fullName: opts.fullName,
    email: opts.email,
    phone: opts.phone,
    departmentId: opts.departmentId,
    designation: opts.designation || opts.role,
    passwordHash,
    role: opts.role,
    status: "ACTIVE",
    createdAt: now(),
    updatedAt: now(),
  };
  users.push(user);
  return user;
}

async function ensureVehicle(vehicles: any[], opts: Record<string, unknown> & { registrationNumber: string }) {
  const existing = vehicles.find((v) => v.registrationNumber === opts.registrationNumber);
  if (existing) return existing;
  const id = await nextId("VEH", 3);
  const vehicle = { id, status: "AVAILABLE", createdAt: now(), updatedAt: now(), ...opts };
  vehicles.push(vehicle);
  return vehicle;
}

async function ensureDriver(drivers: any[], opts: Record<string, unknown> & { licenseNumber: string }) {
  const existing = drivers.find((d) => d.licenseNumber === opts.licenseNumber);
  if (existing) return existing;
  const id = await nextId("DRV", 3);
  const driver = { id, status: "AVAILABLE", createdAt: now(), updatedAt: now(), ...opts };
  drivers.push(driver);
  return driver;
}

async function main() {
  const departments = await readJson("departments");
  const users = await readJson("users");
  const vehicles = await readJson("vehicles");
  const drivers = await readJson("drivers");

  const admin = await ensureDepartment(departments, "ADMIN", "Administration");
  const ops = await ensureDepartment(departments, "OPS", "Operations");
  const sales = await ensureDepartment(departments, "SALES", "Sales");
  await writeJson("departments", departments);

  await ensureUser(users, { fullName: "Super Admin", email: "admin@fleet.local", phone: "01700000001", role: "SUPER_ADMIN", departmentId: admin.id, designation: "System Administrator" });
  await ensureUser(users, { fullName: "Admin User", email: "admin.user@fleet.local", phone: "01700000002", role: "ADMIN", departmentId: admin.id, designation: "Fleet Admin" });
  await ensureUser(users, { fullName: "Transport Manager", email: "manager@fleet.local", phone: "01700000003", role: "TRANSPORT_MANAGER", departmentId: ops.id, designation: "Transport Manager" });
  await ensureUser(users, { fullName: "Employee Demo", email: "employee@fleet.local", phone: "01700000004", role: "EMPLOYEE", departmentId: sales.id, designation: "Sales Executive" });
  const driverUser = await ensureUser(users, { fullName: "Driver Demo", email: "driver@fleet.local", phone: "01700000005", role: "DRIVER", departmentId: ops.id, designation: "Driver" });
  await writeJson("users", users);

  const v1 = await ensureVehicle(vehicles, {
    registrationNumber: "DHAKA-METRO-GA-11-1234",
    vehicleName: "Toyota Noah",
    brand: "Toyota",
    model: "Noah",
    modelYear: 2019,
    vehicleType: "Microbus",
    color: "White",
    seatingCapacity: 7,
    fuelType: "Octane",
    currentKm: 42000,
    assignedDepartmentId: ops.id,
    insuranceExpiry: "2027-01-15",
    fitnessExpiry: "2027-03-01",
    taxTokenExpiry: "2026-12-31",
  });
  await ensureVehicle(vehicles, {
    registrationNumber: "DHAKA-METRO-GA-11-5678",
    vehicleName: "Toyota Axio",
    brand: "Toyota",
    model: "Axio",
    modelYear: 2021,
    vehicleType: "Sedan",
    color: "Silver",
    seatingCapacity: 4,
    fuelType: "Hybrid",
    currentKm: 18500,
    assignedDepartmentId: sales.id,
    insuranceExpiry: "2027-05-20",
    fitnessExpiry: "2027-06-01",
    taxTokenExpiry: "2026-11-30",
  });
  await ensureVehicle(vehicles, {
    registrationNumber: "DHAKA-METRO-GA-22-9012",
    vehicleName: "Hino Truck",
    brand: "Hino",
    model: "300 Series",
    modelYear: 2018,
    vehicleType: "Other",
    color: "Blue",
    seatingCapacity: 2,
    fuelType: "Diesel",
    currentKm: 88000,
    assignedDepartmentId: ops.id,
    insuranceExpiry: "2026-10-01",
    fitnessExpiry: "2026-10-15",
    taxTokenExpiry: "2026-09-30",
  });

  await ensureDriver(drivers, {
    userId: driverUser.id,
    driverName: "Driver Demo",
    phone: "01700000005",
    email: "driver@fleet.local",
    licenseNumber: "DL-2025-00123",
    licenseType: "Professional",
    licenseExpiryDate: "2028-01-01",
    joiningDate: "2023-01-01",
    assignedVehicleId: v1.id,
    emergencyContact: "01700000009",
  });
  await ensureDriver(drivers, {
    driverName: "Karim Ahmed",
    phone: "01700000006",
    licenseNumber: "DL-2024-00987",
    licenseType: "Professional",
    licenseExpiryDate: "2027-06-01",
    joiningDate: "2022-05-01",
    emergencyContact: "01700000010",
  });

  await writeJson("vehicles", vehicles);
  await writeJson("drivers", drivers);

  console.log(`Seed complete. Demo accounts (password: Passw0rd!):
  SUPER_ADMIN         admin@fleet.local
  ADMIN               admin.user@fleet.local
  TRANSPORT_MANAGER   manager@fleet.local
  EMPLOYEE            employee@fleet.local
  DRIVER              driver@fleet.local`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
