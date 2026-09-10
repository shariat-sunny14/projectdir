import { redirect } from "next/navigation";
import { getSession } from "@/lib/auth/session";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { MobileNav } from "@/components/layout/mobile-nav";

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const session = await getSession();
  if (!session) {
    redirect("/login");
  }

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar role={session.role} />
      <div className="flex min-h-screen flex-1 flex-col">
        <Header session={session} />
        <main className="flex-1 overflow-y-auto p-4 pb-20 sm:p-6 md:pb-6">
          <div className="mx-auto max-w-6xl animate-fade-in-up">{children}</div>
        </main>
      </div>
      <MobileNav role={session.role} />
    </div>
  );
}
