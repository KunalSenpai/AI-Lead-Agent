import { supabase } from "../lib/supabase";

export async function getAccessToken(): Promise<string | null> {
  const {
    data: { session },
    error,
  } = await supabase.auth.getSession();

  if (error) {
    console.error("Failed to get Supabase session:", error);
    return null;
  }

  return session?.access_token ?? null;
}