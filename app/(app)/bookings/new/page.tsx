import { redirect } from "next/navigation";
import { getSession } from "@/lib/auth/session";
import { usersRepo, departmentsRepo } from "@/lib/json-db/repositories";
import { BookingWizard } from "./booking-wizard";

export default async function NewBookingPage() {
  const session = await getSession();
  if (!session) redirect("/login");

  const user = await usersRepo.findById(session.userId);
  const departments = await departmentsRepo.findAll();
  const departmentName = departments.find((d) => d.id === user?.departmentId)?.name || "—";

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">New Booking</h1>
        <p className="text-sm text-slate-500">Request a vehicle for your trip. Final assignment is confirmed by an admin.</p>
      </div>

      <BookingWizard employeeName={session.fullName} departmentName={departmentName} />
    </div>
  );
}
