import { useState, useEffect, useCallback } from 'react';

interface UseApiDataResult<T> {
  data: T | null;
  loading: boolean;
  error: boolean;
}

/**
 * Generic polling hook that fetches a JSON endpoint on mount and on a
 * configurable interval.  Re-fetches whenever `url` changes.
 *
 * @param url        - Full URL to fetch, or `null` to skip fetching.
 * @param refreshMs  - Polling interval in milliseconds (default: 5000).
 */
export function useApiData<T>(
  url: string | null,
  refreshMs: number = 5000
): UseApiDataResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const fetchData = useCallback(async () => {
    if (!url) return;
    try {
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json: T = await res.json();
      setData(json);
      setError(false);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  }, [url]);

  useEffect(() => {
    setLoading(true);
    setData(null);
    fetchData();
    const iv = setInterval(fetchData, refreshMs);
    return () => clearInterval(iv);
  }, [fetchData, refreshMs]);

  return { data, loading, error };
}
