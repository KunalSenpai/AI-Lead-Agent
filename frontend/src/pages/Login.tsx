import { FormEvent, useState } from "react";
import { supabase } from "../lib/supabase";

const BASE = (
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000"
).replace(/\/$/, "");

export function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();

    setLoading(true);
    setError(null);

    try {
      // -----------------------------------------
      // Step 1: Sign in with Supabase
      // -----------------------------------------

      const { data, error: loginError } =
        await supabase.auth.signInWithPassword({
          email,
          password,
        });

      if (loginError) {
        setError(loginError.message);
        return;
      }

      // -----------------------------------------
      // Step 2: Make sure we received a session
      // -----------------------------------------

      const accessToken = data.session?.access_token;

      if (!accessToken) {
        setError(
          "Login succeeded but no access token was returned."
        );
        return;
      }

      // -----------------------------------------
      // Step 3: Send token to FastAPI
      // -----------------------------------------
      const response = await fetch(
        `${BASE}/auth/me`,
        {
          method: "GET",
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        }
      );

      // -----------------------------------------
      // Step 4: Check backend authentication
      // -----------------------------------------

      if (!response.ok) {
        const detail = await response.text();

        setError(
          `Backend authentication failed (${response.status}): ${detail}`
        );

        return;
      }

      // -----------------------------------------
      // Step 5: Read authenticated user
      // -----------------------------------------

      const backendUser = await response.json();

      console.log(
        "Backend authenticated user:",
        backendUser
      );

      // -----------------------------------------
      // Step 6: Login successful
      // -----------------------------------------

      window.location.href = "/dashboard";

    } catch (error) {
      console.error(
        "Login failed:",
        error
      );

      setError(
        error instanceof Error
          ? error.message
          : "Login failed"
      );

    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h1>AI Lead Agent</h1>

      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="email">
            Email
          </label>

          <input
            id="email"
            type="email"
            value={email}
            onChange={(event) =>
              setEmail(event.target.value)
            }
            required
          />
        </div>

        <div>
          <label htmlFor="password">
            Password
          </label>

          <input
            id="password"
            type="password"
            value={password}
            onChange={(event) =>
              setPassword(event.target.value)
            }
            required
          />
        </div>

        {error && (
          <p>
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={loading}
        >
          {loading
            ? "Signing in..."
            : "Sign in"}
        </button>
      </form>
    </div>
  );
}