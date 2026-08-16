import { useCallback, useEffect, useState } from "react";
import type { Lead } from "../types/lead";
import { getLead, ApiError } from "../services/leadsApi";

export function useLead(id: number) {
  const [lead, setLead] = useState<Lead | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getLead(id);
      setLead(data);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Unable to load this lead. Please try again.");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  return { lead, setLead, loading, error, reload: load };
}
