import { redirect } from "next/navigation";
import { getSession } from "@/lib/auth/session";
import { canApproveBookings } from "@/lib/permissions";
import { getActiveTrackedVehicles } from "@/lib/services/tracking-service";
import { LiveTrackingMap } from "./live-tracking-map";

export default async function LiveTrackingPage() {
  const session = await getSession();
  if (!session) redirect("/login");
  if (!canApproveBookings(session.role)) redirect("/dashboard");

  const initial = await getActiveTrackedVehicles();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">Live Fleet Tracking</h1>
        <p className="text-sm text-slate-500">Real-time position of every vehicle currently on a trip. Refreshes automatically.</p>
      </div>

      <LiveTrackingMap initial={initial} />
    </div>
  );
}
