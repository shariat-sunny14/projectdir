import { readJson, updateJson } from "./core";

export interface BaseRecord {
  id: string;
  createdAt: string;
  updatedAt: string;
}

/** Generic repository factory for a JSON-file-backed collection. */
export function createRepository<T extends BaseRecord>(fileName: string) {
  return {
    async findAll(): Promise<T[]> {
      return readJson<T[]>(fileName);
    },

    async findById(id: string): Promise<T | undefined> {
      const all = await readJson<T[]>(fileName);
      return all.find((r) => r.id === id);
    },

    async findOne(predicate: (r: T) => boolean): Promise<T | undefined> {
      const all = await readJson<T[]>(fileName);
      return all.find(predicate);
    },

    async findMany(predicate: (r: T) => boolean): Promise<T[]> {
      const all = await readJson<T[]>(fileName);
      return all.filter(predicate);
    },

    async insert(record: T): Promise<T> {
      return updateJson<T[]>(fileName, (all) => {
        all.push(record);
        return all;
      }).then(() => record);
    },

    async update(id: string, patch: Partial<T>): Promise<T | undefined> {
      let updated: T | undefined;
      await updateJson<T[]>(fileName, (all) => {
        const idx = all.findIndex((r) => r.id === id);
        if (idx === -1) return all;
        updated = {
          ...all[idx],
          ...patch,
          updatedAt: new Date().toISOString(),
        };
        all[idx] = updated;
        return all;
      });
      return updated;
    },

    async remove(id: string): Promise<boolean> {
      let removed = false;
      await updateJson<T[]>(fileName, (all) => {
        const idx = all.findIndex((r) => r.id === id);
        if (idx === -1) return all;
        removed = true;
        all.splice(idx, 1);
        return all;
      });
      return removed;
    },
  };
}
