import { useEffect, useState } from "react";

import {
  disconnectGmail,
  getGmailStatus,
} from "../api";


export function Settings() {

  const apiBaseUrl =
    import.meta.env.VITE_API_BASE_URL ||
    "http://127.0.0.1:8000";

  const [gmailConnected, setGmailConnected] =
    useState(false);

  const [gmailEmail, setGmailEmail] =
    useState<string | null>(null);

  const [loading, setLoading] =
    useState(true);

  const [disconnecting, setDisconnecting] =
    useState(false);

  const [gmailError, setGmailError] =
    useState<string | null>(null);


  // -------------------------------------------------------
  // Load Gmail connection status
  // -------------------------------------------------------

  useEffect(() => {

    async function loadGmailStatus() {

      try {

        setLoading(true);
        setGmailError(null);

        const status = await getGmailStatus();

        setGmailConnected(
          status.connected
        );

        setGmailEmail(
          status.gmail_email
        );

      } catch (error) {

        console.error(
          "Failed to load Gmail status:",
          error
        );

        setGmailConnected(false);
        setGmailEmail(null);

        setGmailError(
          error instanceof Error
            ? error.message
            : "Failed to check Gmail connection."
        );

      } finally {

        setLoading(false);

      }
    }

    loadGmailStatus();

  }, []);


  // -------------------------------------------------------
  // Disconnect Gmail
  // -------------------------------------------------------

  async function handleDisconnectGmail() {

    const confirmed = window.confirm(
      "Are you sure you want to disconnect this Gmail account?"
    );

    if (!confirmed) {
      return;
    }

    try {

      setDisconnecting(true);
      setGmailError(null);

      await disconnectGmail();

      setGmailConnected(false);
      setGmailEmail(null);

    } catch (error) {

      console.error(
        "Failed to disconnect Gmail:",
        error
      );

      setGmailError(
        error instanceof Error
          ? error.message
          : "Failed to disconnect Gmail."
      );

    } finally {

      setDisconnecting(false);

    }
  }


  // -------------------------------------------------------
  // Connect Gmail
  // -------------------------------------------------------

  async function handleConnectGmail() {

    try {

      setGmailError(null);

      const apiBase =
        apiBaseUrl.replace(/\/$/, "");

      /*
       * We need the authenticated access token here.
       * The /gmail/connect endpoint requires the current
       * application user.
       */

      const {
        supabase,
      } = await import("../lib/supabase");

      const {
        data: {
          session,
        },
      } = await supabase.auth.getSession();

      if (!session?.access_token) {

        setGmailError(
          "You must be signed in to connect Gmail."
        );

        return;
      }

      const response = await fetch(
        `${apiBase}/gmail/connect`,
        {
          method: "GET",

          headers: {
            Authorization:
              `Bearer ${session.access_token}`,
          },
        }
      );

      const data =
        await response
          .json()
          .catch(() => null);

      if (!response.ok) {

        throw new Error(
          data?.detail ||
          "Failed to start Gmail connection."
        );

      }

      if (!data?.authorization_url) {

        throw new Error(
          "Google authorization URL was not returned."
        );

      }

      /*
       * Send the browser to Google's OAuth page.
       */

      window.location.href =
        data.authorization_url;

    } catch (error) {

      console.error(
        "Failed to connect Gmail:",
        error
      );

      setGmailError(
        error instanceof Error
          ? error.message
          : "Failed to connect Gmail."
      );
    }
  }


  // -------------------------------------------------------
  // Render
  // -------------------------------------------------------

  return (
    <div style={{ maxWidth: 480 }}>

      <div className="page-header">
        <h2>Settings</h2>
      </div>


      {/* ================================================= */}
      {/* Backend connection                                */}
      {/* ================================================= */}

      <div className="card">

        <div className="card-title">
          Connection
        </div>


        <div className="kv-label">
          Backend API URL
        </div>

        <div className="kv-value tabular">
          {apiBaseUrl}
        </div>


        <p
          style={{
            marginTop: 12,
            fontSize: 12.5,
            color: "var(--text-tertiary)",
          }}
        >
          Configured via the
          VITE_API_BASE_URL environment variable.
        </p>

      </div>


      {/* ================================================= */}
      {/* Gmail connection                                   */}
      {/* ================================================= */}

      <div
        className="card"
        style={{
          marginTop: 16,
        }}
      >

        <div className="card-title">
          Gmail
        </div>


        {/* ----------------------------------------------- */}
        {/* Loading                                          */}
        {/* ----------------------------------------------- */}

        {loading ? (

          <div
            style={{
              marginTop: 12,
              fontSize: 14,
              color: "var(--text-secondary)",
            }}
          >
            Checking Gmail connection...
          </div>

        ) : gmailConnected ? (

          /* --------------------------------------------- */
          /* Connected                                       */
          /* --------------------------------------------- */

          <>

            <div className="kv-label">
              Status
            </div>

            <div
              className="kv-value"
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
              }}
            >

              <span
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: "50%",
                  background: "var(--success, #22c55e)",
                  display: "inline-block",
                }}
              />

              Connected

            </div>


            {gmailEmail && (

              <>

                <div
                  className="kv-label"
                  style={{
                    marginTop: 14,
                  }}
                >
                  Gmail account
                </div>

                <div className="kv-value">
                  {gmailEmail}
                </div>

              </>

            )}


            {/* ----------------------------------------- */}
            {/* Disconnect button                           */}
            {/* ----------------------------------------- */}

            <div
              style={{
                marginTop: 20,
              }}
            >

              <button
                type="button"
                onClick={
                  handleDisconnectGmail
                }
                disabled={disconnecting}
                className="btn-secondary"
              >
                {disconnecting
                  ? "Disconnecting..."
                  : "Disconnect Gmail"}
              </button>

            </div>

          </>

        ) : (

          /* --------------------------------------------- */
          /* Not connected                                  */
          /* --------------------------------------------- */

          <>

            <div className="kv-label">
              Status
            </div>

            <div className="kv-value">
              Not connected
            </div>


            <p
              style={{
                marginTop: 12,
                fontSize: 13,
                color: "var(--text-tertiary)",
                lineHeight: 1.5,
              }}
            >
              Connect a Gmail account to sync
              incoming leads and send approved
              emails.
            </p>


            {/* ----------------------------------------- */}
            {/* Connect button                              */}
            {/* ----------------------------------------- */}

            <div
              style={{
                marginTop: 18,
              }}
            >

              <button
                type="button"
                onClick={
                  handleConnectGmail
                }
                className="btn-primary"
              >
                Connect Gmail
              </button>

            </div>

          </>

        )}


        {/* ================================================= */}
        {/* Gmail error                                       */}
        {/* ================================================= */}

        {gmailError && (

          <div
            style={{
              marginTop: 14,
              padding: "10px 12px",
              borderRadius: 8,
              fontSize: 13,
              color: "var(--danger, #ef4444)",
              background:
                "var(--danger-bg, rgba(239, 68, 68, 0.08))",
            }}
          >
            {gmailError}
          </div>

        )}

      </div>

    </div>
  );
}