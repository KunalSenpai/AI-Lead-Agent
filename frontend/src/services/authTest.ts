import { getAccessToken } from "./authApi";

export async function testAuthenticatedBackend(): Promise<void> {
  const token = await getAccessToken();

  if (!token) {
    throw new Error("No Supabase access token found");
  }

  const response = await fetch(
    "http://127.0.0.1:8000/auth/me",
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  if (!response.ok) {
    throw new Error(
      `Authentication test failed: ${response.status}`
    );
  }

  const data = await response.json();

  console.log("Authenticated backend user:", data);
}