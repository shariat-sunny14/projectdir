"use server";

import { revalidatePath } from "next/cache";
import { getSession } from "@/lib/auth/session";
import { markNotificationRead, markAllNotificationsRead, getNotificationsForUser } from "@/lib/services/notification-service";

export async function fetchNotificationsAction() {
  const session = await getSession();
  if (!session) return [];
  return getNotificationsForUser(session.userId);
}

export async function markNotificationReadAction(id: string) {
  await markNotificationRead(id);
  revalidatePath("/dashboard");
}

export async function markAllNotificationsReadAction() {
  const session = await getSession();
  if (!session) return;
  await markAllNotificationsRead(session.userId);
  revalidatePath("/dashboard");
}
