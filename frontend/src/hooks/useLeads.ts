import { useCallback, useEffect, useState } from "react";
import type { Lead } from "../types/lead";
import { getLeads, ApiError } from "../services/leadsApi";

export function useLeads(status?: string) {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getLeads(status);
      setLeads(data);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Unable to load leads. Please try again.");
    } finally {
      setLoading(false);
    }
  }, [status]);

  useEffect(() => {
    load();
  }, [load]);

  return { leads, loading, error, reload: load };
}
