/** Fetches the discovery feed from the real API, with abort + retry support. */
import { useCallback, useEffect, useState } from "react";
import { api, ApiError } from "../api/client";
import type { DiscoverResponse } from "../api/types";
import { EMPTY_CRITERIA, useSession, type SearchCriteria } from "../state/SessionContext";

export interface DiscoverState {
  data: DiscoverResponse | null;
  loading: boolean;
  error: string | null;
  retry: () => void;
}

export function useDiscover(): DiscoverState {
  const { criteria } = useSession();
  const [data, setData] = useState<DiscoverResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [nonce, setNonce] = useState(0);
  const { setLastResults } = useSession();
  const criteriaKey = JSON.stringify(criteria);

  useEffect(() => {
    const controller = new AbortController();
    const parsed: SearchCriteria = { ...EMPTY_CRITERIA, ...JSON.parse(criteriaKey) };

    setLoading(true);
    setError(null);

    api
      .discover(
        {
          q: parsed.q,
          budget: parsed.budget ?? undefined,
          currency: "PKR",
          condition: parsed.condition,
          mustHave: parsed.mustHave,
          niceToHave: parsed.niceToHave,
          minRam: parsed.minRam ?? undefined,
          minStorage: parsed.minStorage ?? undefined,
          maxWeight: parsed.maxWeight ?? undefined,
          minScreen: parsed.minScreen ?? undefined,
          sort: parsed.sort,
        },
        controller.signal,
      )
      .then((response) => {
        setData(response);
        setLastResults(
          response.results.map((r) => ({
            productId: r.product.product_id,
            name: r.product.name,
          })),
        );
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        if (err instanceof ApiError) {
          setError(err.detail ? `${err.message}: ${err.detail}` : err.message);
        } else {
          setError("Something went wrong while loading results.");
        }
        setData(null);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });

    return () => controller.abort();
    // criteriaKey is a stable serialisation of criteria.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [criteriaKey, nonce]);

  const retry = useCallback(() => setNonce((n) => n + 1), []);

  return { data, loading, error, retry };
}