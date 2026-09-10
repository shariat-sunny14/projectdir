import { notificationsRepo } from "@/lib/json-db/repositories";
import { nextId } from "@/lib/json-db/core";
import type { NotificationType } from "@/lib/types";

export async function createNotification(
  userId: string,
  title: string,
  message: string,
  type: NotificationType,
  relatedId?: string
) {
  const id = await nextId("NOT");
  const now = new Date().toISOString();
  return notificationsRepo.insert({
    id,
    userId,
    title,
    message,
    type,
    relatedId,
    isRead: false,
    createdAt: now,
    updatedAt: now,
  });
}

export async function getNotificationsForUser(userId: string) {
  const all = await notificationsRepo.findMany((n) => n.userId === userId);
  return all.sort((a, b) => b.createdAt.localeCompare(a.createdAt));
}

export async function markNotificationRead(id: string) {
  return notificationsRepo.update(id, { isRead: true });
}

export async function markAllNotificationsRead(userId: string) {
  const mine = await notificationsRepo.findMany((n) => n.userId === userId && !n.isRead);
  await Promise.all(mine.map((n) => notificationsRepo.update(n.id, { isRead: true })));
}
