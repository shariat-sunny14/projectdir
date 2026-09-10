import { auditLogsRepo } from "@/lib/json-db/repositories";
import { nextId } from "@/lib/json-db/core";
import type { AuditAction } from "@/lib/types";

export async function writeAudit(
  userId: string,
  module: string,
  action: AuditAction | string,
  recordId: string,
  description?: string
) {
  const id = await nextId("AUD");
  const now = new Date().toISOString();
  await auditLogsRepo.insert({
    id,
    userId,
    module,
    action,
    recordId,
    description,
    createdAt: now,
    updatedAt: now,
  });
}
