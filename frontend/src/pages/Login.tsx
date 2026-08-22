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
  const [showPassword, setShowPassword] = useState(false);

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
      console.error("Login failed:", error);

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
    <div className="login-page">
      <style>{`
        .login-page {
          min-height: 100vh;
          width: 100%;
          display: flex;
          flex-direction: column;
          background: #f7f8fa;
          color: #111827;
          font-family:
            Inter,
            ui-sans-serif,
            system-ui,
            -apple-system,
            BlinkMacSystemFont,
            "Segoe UI",
            sans-serif;
        }

        .login-header {
          height: 64px;
          display: flex;
          align-items: center;
          padding: 0 32px;
          background: #ffffff;
          border-bottom: 1px solid #e5e7eb;
          box-sizing: border-box;
        }

        .login-brand {
          display: flex;
          align-items: center;
          gap: 10px;
          color: #4f46e5;
          font-size: 16px;
          font-weight: 650;
          letter-spacing: -0.01em;
        }

        .login-brand-mark {
          width: 30px;
          height: 30px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 8px;
          background: #4f46e5;
          color: #ffffff;
        }

        .login-brand-mark svg {
          width: 17px;
          height: 17px;
        }

        .login-content {
          flex: 1;
          display: flex;
          justify-content: center;
          align-items: flex-start;
          padding: 72px 24px;
          box-sizing: border-box;
        }

        .login-card {
          width: 100%;
          max-width: 440px;
          padding: 36px;
          box-sizing: border-box;
          background: #ffffff;
          border: 1px solid #e5e7eb;
          border-radius: 14px;
          box-shadow:
            0 4px 16px rgba(15, 23, 42, 0.04),
            0 1px 3px rgba(15, 23, 42, 0.03);
        }

        .login-card-header {
          margin-bottom: 30px;
        }

        .login-card-title {
          margin: 0;
          color: #111827;
          font-size: 25px;
          line-height: 1.25;
          font-weight: 700;
          letter-spacing: -0.025em;
        }

        .login-card-description {
          margin: 9px 0 0;
          color: #6b7280;
          font-size: 14px;
          line-height: 1.6;
        }

        .login-form {
          display: flex;
          flex-direction: column;
          gap: 19px;
        }

        .login-field {
          display: flex;
          flex-direction: column;
          gap: 7px;
        }

        .login-label {
          color: #374151;
          font-size: 13px;
          font-weight: 600;
        }

        .login-input-wrapper {
          position: relative;
        }

        .login-input {
          width: 100%;
          height: 45px;
          padding: 0 13px;
          box-sizing: border-box;

          border: 1px solid #d1d5db;
          border-radius: 8px;

          outline: none;
          background: #ffffff;
          color: #111827;

          font-family: inherit;
          font-size: 14px;

          transition:
            border-color 150ms ease,
            box-shadow 150ms ease,
            background 150ms ease;
        }

        .login-input::placeholder {
          color: #9ca3af;
        }

        .login-input:hover {
          border-color: #b8bec8;
        }

        .login-input:focus {
          border-color: #6366f1;
          background: #ffffff;
          box-shadow:
            0 0 0 3px rgba(99, 102, 241, 0.10);
        }

        .login-input:disabled {
          background: #f9fafb;
          cursor: not-allowed;
        }

        .password-input {
          padding-right: 46px;
        }

        .password-toggle {
          position: absolute;
          right: 6px;
          top: 50%;
          width: 34px;
          height: 34px;
          display: flex;
          align-items: center;
          justify-content: center;
          transform: translateY(-50%);

          border: 0;
          border-radius: 7px;
          background: transparent;
          color: #6b7280;
          cursor: pointer;
        }

        .password-toggle:hover {
          background: #f3f4f6;
          color: #374151;
        }

        .password-toggle:focus-visible {
          outline: 2px solid #6366f1;
          outline-offset: 1px;
        }

        .password-toggle:disabled {
          cursor: not-allowed;
        }

        .password-toggle svg {
          width: 17px;
          height: 17px;
        }

        .login-error {
          padding: 11px 13px;
          border: 1px solid #fecaca;
          border-radius: 8px;
          background: #fef2f2;
          color: #b91c1c;
          font-size: 13px;
          line-height: 1.5;
        }

        .login-submit {
          width: 100%;
          height: 45px;
          margin-top: 3px;

          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;

          border: 0;
          border-radius: 8px;

          background: #4f46e5;
          color: #ffffff;

          font-family: inherit;
          font-size: 14px;
          font-weight: 600;

          cursor: pointer;

          box-shadow:
            0 2px 5px rgba(79, 70, 229, 0.18);

          transition:
            background 150ms ease,
            transform 150ms ease,
            box-shadow 150ms ease;
        }

        .login-submit:hover:not(:disabled) {
          background: #4338ca;
          box-shadow:
            0 4px 10px rgba(79, 70, 229, 0.22);
          transform: translateY(-1px);
        }

        .login-submit:active:not(:disabled) {
          transform: translateY(0);
        }

        .login-submit:focus-visible {
          outline: 2px solid #818cf8;
          outline-offset: 3px;
        }

        .login-submit:disabled {
          background: #a5b4fc;
          cursor: not-allowed;
        }

        .login-spinner {
          width: 15px;
          height: 15px;
          border: 2px solid rgba(255, 255, 255, 0.35);
          border-top-color: #ffffff;
          border-radius: 50%;
          animation: login-spin 700ms linear infinite;
        }

        @keyframes login-spin {
          to {
            transform: rotate(360deg);
          }
        }

        .login-footer {
          margin-top: 26px;
          padding-top: 20px;
          border-top: 1px solid #f0f1f3;
          text-align: center;
          color: #9ca3af;
          font-size: 12px;
          line-height: 1.5;
        }

        @media (max-width: 600px) {
          .login-header {
            padding: 0 20px;
          }

          .login-content {
            padding: 40px 16px;
          }

          .login-card {
            padding: 28px 22px;
            border-radius: 12px;
          }

          .login-card-title {
            font-size: 23px;
          }
        }

        @media (prefers-reduced-motion: reduce) {
          .login-input,
          .login-submit {
            transition: none;
          }

          .login-spinner {
            animation: none;
          }
        }
      `}</style>

      {/* Header */}
      <header className="login-header">
        <div className="login-brand">
          <span className="login-brand-mark">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M12 3v3" />
              <path d="M12 18v3" />
              <path d="M3 12h3" />
              <path d="M18 12h3" />
              <circle cx="12" cy="12" r="4" />
            </svg>
          </span>

          AI Lead Agent
        </div>
      </header>

      {/* Login content */}
      <main className="login-content">
        <section className="login-card">
          <div className="login-card-header">
            <h1 className="login-card-title">
              Welcome back
            </h1>

            <p className="login-card-description">
              Sign in to continue to your AI Lead Agent
              workspace.
            </p>
          </div>

          <form
            className="login-form"
            onSubmit={handleSubmit}
          >
            {/* Email */}
            <div className="login-field">
              <label
                className="login-label"
                htmlFor="email"
              >
                Email
              </label>

              <input
                className="login-input"
                id="email"
                type="email"
                value={email}
                onChange={(event) =>
                  setEmail(event.target.value)
                }
                placeholder="you@example.com"
                autoComplete="email"
                required
                disabled={loading}
              />
            </div>

            {/* Password */}
            <div className="login-field">
              <label
                className="login-label"
                htmlFor="password"
              >
                Password
              </label>

              <div className="login-input-wrapper">
                <input
                  className="login-input password-input"
                  id="password"
                  type={
                    showPassword
                      ? "text"
                      : "password"
                  }
                  value={password}
                  onChange={(event) =>
                    setPassword(event.target.value)
                  }
                  placeholder="Enter your password"
                  autoComplete="current-password"
                  required
                  disabled={loading}
                />

                <button
                  type="button"
                  className="password-toggle"
                  onClick={() =>
                    setShowPassword(
                      (current) => !current
                    )
                  }
                  aria-label={
                    showPassword
                      ? "Hide password"
                      : "Show password"
                  }
                  disabled={loading}
                >
                  {showPassword ? (
                    <svg
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1.8"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      aria-hidden="true"
                    >
                      <path d="M3 3l18 18" />
                      <path d="M10.6 10.6a2 2 0 0 0 2.8 2.8" />
                      <path d="M9.9 4.3A9.7 9.7 0 0 1 12 4c5 0 8.5 4 9.5 8a11.6 11.6 0 0 1-3 4.8" />
                      <path d="M6.6 6.6C4.6 8 3.3 10.1 2.5 12c1 4 4.5 8 9.5 8a9.5 9.5 0 0 0 3-.5" />
                    </svg>
                  ) : (
                    <svg
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1.8"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      aria-hidden="true"
                    >
                      <path d="M2.5 12s3.5-7 9.5-7 9.5 7 9.5 7-3.5 7-9.5 7-9.5-7-9.5-7Z" />
                      <circle
                        cx="12"
                        cy="12"
                        r="2.5"
                      />
                    </svg>
                  )}
                </button>
              </div>
            </div>

            {/* Error */}
            {error && (
              <div
                className="login-error"
                role="alert"
              >
                {error}
              </div>
            )}

            {/* Submit */}
            <button
              className="login-submit"
              type="submit"
              disabled={loading}
            >
              {loading ? (
                <>
                  <span
                    className="login-spinner"
                    aria-hidden="true"
                  />
                  Signing in...
                </>
              ) : (
                "Sign in"
              )}
            </button>
          </form>

          <div className="login-footer">
            AI-powered lead research, scoring, and
            outreach.
          </div>
        </section>
      </main>
    </div>
  );
}