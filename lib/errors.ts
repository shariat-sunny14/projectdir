export type ErrorCode =
  | "ERR_ACCOUNT_PENDING"
  | "ERR_ACCOUNT_REJECTED"
  | "ERR_ACCOUNT_SUSPENDED"
  | "ERR_INVALID_CREDENTIALS"
  | "ERR_DUPLICATE_EMAIL"
  | "ERR_VEHICLE_CONFLICT"
  | "ERR_DRIVER_CONFLICT"
  | "ERR_VEHICLE_UNAVAILABLE"
  | "ERR_DRIVER_UNAVAILABLE"
  | "ERR_INVALID_RANGE"
  | "ERR_KM_INVALID"
  | "ERR_BOOKING_NOT_EDITABLE"
  | "ERR_BOOKING_NOT_CANCELABLE"
  | "ERR_FORBIDDEN"
  | "ERR_NOT_FOUND"
  | "ERR_STORAGE"
  | "ERR_EMAIL"
  | "ERR_VALIDATION";

/** Standard application error. Thrown by services, caught by Server Actions,
 * and converted into the standard { ok: false, error: {...} } shape. */
export class AppError extends Error {
  code: ErrorCode;
  field?: string;

  constructor(code: ErrorCode, message: string, field?: string) {
    super(message);
    this.code = code;
    this.field = field;
  }
}

export interface ActionSuccess<T> {
  ok: true;
  data: T;
}

export interface ActionFailure {
  ok: false;
  error: { code: ErrorCode | "ERR_UNKNOWN"; message: string; field?: string };
}

export type ActionResult<T> = ActionSuccess<T> | ActionFailure;

export function ok<T>(data: T): ActionSuccess<T> {
  return { ok: true, data };
}

export function toActionFailure(err: unknown): ActionFailure {
  if (err instanceof AppError) {
    return { ok: false, error: { code: err.code, message: err.message, field: err.field } };
  }
  return {
    ok: false,
    error: { code: "ERR_UNKNOWN", message: err instanceof Error ? err.message : "Unexpected error." },
  };
}

/** Runs a service call and always returns the standard ActionResult shape,
 * so a thrown AppError never becomes an unhandled server-action rejection. */
export async function runAction<T>(fn: () => Promise<T>): Promise<ActionResult<T>> {
  try {
    const data = await fn();
    return ok(data);
  } catch (err) {
    return toActionFailure(err);
  }
}
