import {
  Menu,
  Bell,
  CircleUserRound,
} from "lucide-react";

import {
  useEffect,
  useRef,
  useState,
} from "react";

import { useNavigate } from "react-router-dom";

import { supabase } from "../../lib/supabase";
import { getLeads } from "../../api";

import type { Lead } from "../../types";


interface TopbarProps {
  title: string;
  onMenuClick: () => void;
}


export function Topbar({
  title,
  onMenuClick,
}: TopbarProps) {

  const navigate = useNavigate();

  const [notificationsOpen, setNotificationsOpen] =
    useState(false);

  const [accountOpen, setAccountOpen] =
    useState(false);

  const [pendingCount, setPendingCount] =
    useState(0);

  const [failedCount, setFailedCount] =
    useState(0);

  const [loadingNotifications, setLoadingNotifications] =
    useState(false);

  const notificationsRef =
    useRef<HTMLDivElement | null>(null);

  const accountRef =
    useRef<HTMLDivElement | null>(null);


  // -------------------------------------------------------
  // Load notification counts
  // -------------------------------------------------------

  async function loadNotificationCounts() {

    try {

      setLoadingNotifications(true);

      const leads: Lead[] =
        await getLeads();

      const pending =
        leads.filter(
          (lead) =>
            lead.email_status ===
            "pending_approval"
        ).length;

      const failed =
        leads.filter(
          (lead) =>
            lead.email_status ===
            "failed"
        ).length;

      setPendingCount(pending);
      setFailedCount(failed);

    } catch (error) {

      console.error(
        "Failed to load notifications:",
        error
      );

    } finally {

      setLoadingNotifications(false);

    }
  }


  // -------------------------------------------------------
  // Load counts when Topbar mounts
  // -------------------------------------------------------

  useEffect(() => {

    loadNotificationCounts();

  }, []);


  // -------------------------------------------------------
  // Close dropdowns when clicking outside
  // -------------------------------------------------------

  useEffect(() => {

    function handleClickOutside(
      event: MouseEvent
    ) {

      const target =
        event.target as Node;

      if (
        notificationsRef.current &&
        !notificationsRef.current.contains(
          target
        )
      ) {

        setNotificationsOpen(false);

      }

      if (
        accountRef.current &&
        !accountRef.current.contains(
          target
        )
      ) {

        setAccountOpen(false);

      }
    }

    document.addEventListener(
      "mousedown",
      handleClickOutside
    );

    return () => {

      document.removeEventListener(
        "mousedown",
        handleClickOutside
      );

    };

  }, []);


  // -------------------------------------------------------
  // Toggle notifications
  // -------------------------------------------------------

  function handleNotificationsClick() {

    setNotificationsOpen(
      (current) => !current
    );

    setAccountOpen(false);

    if (!notificationsOpen) {

      loadNotificationCounts();

    }
  }


  // -------------------------------------------------------
  // Toggle account menu
  // -------------------------------------------------------

  function handleAccountClick() {

    setAccountOpen(
      (current) => !current
    );

    setNotificationsOpen(false);

  }


  // -------------------------------------------------------
  // Navigate to Settings
  // -------------------------------------------------------

  function handleSettings() {

    setAccountOpen(false);

    navigate("/settings");

  }


  // -------------------------------------------------------
  // Sign out
  // -------------------------------------------------------

  async function handleSignOut() {

    setAccountOpen(false);

    try {

      const {
        error,
      } = await supabase.auth.signOut();

      if (error) {

        console.error(
          "Failed to sign out:",
          error
        );

        return;
      }

      navigate("/login");

    } catch (error) {

      console.error(
        "Sign out failed:",
        error
      );

    }
  }


  // -------------------------------------------------------
  // Open pending leads
  // -------------------------------------------------------

  function handlePendingLeads() {

    setNotificationsOpen(false);

    navigate("/pending");

  }


  // -------------------------------------------------------
  // Total notification count
  // -------------------------------------------------------

  const notificationCount =
    pendingCount + failedCount;


  return (
    <header className="topbar">

      {/* ================================================= */}
      {/* Mobile menu                                       */}
      {/* ================================================= */}

      <button
        className="topbar-menu-btn"
        onClick={onMenuClick}
        aria-label="Open menu"
      >
        <Menu size={20} />
      </button>


      {/* ================================================= */}
      {/* Page title                                        */}
      {/* ================================================= */}

      <h1 className="topbar-title">
        {title}
      </h1>


      {/* ================================================= */}
      {/* Actions                                           */}
      {/* ================================================= */}

      <div className="topbar-actions">


        {/* =============================================== */}
        {/* Notifications                                   */}
        {/* =============================================== */}

        <div
          ref={notificationsRef}
          style={{
            position: "relative",
          }}
        >

          <button
            className="icon-btn"
            aria-label="Notifications"
            aria-expanded={
              notificationsOpen
            }
            onClick={
              handleNotificationsClick
            }
          >

            <Bell size={18} />


            {notificationCount > 0 && (

              <span
                style={{
                  position: "absolute",
                  top: 2,
                  right: 2,
                  minWidth: 16,
                  height: 16,
                  padding: "0 4px",
                  borderRadius: 999,
                  background:
                    "var(--danger, #ef4444)",
                  color: "#fff",
                  fontSize: 9,
                  fontWeight: 700,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  lineHeight: 1,
                }}
              >
                {notificationCount > 99
                  ? "99+"
                  : notificationCount}
              </span>

            )}

          </button>


          {/* --------------------------------------------- */}
          {/* Notification dropdown                         */}
          {/* --------------------------------------------- */}

          {notificationsOpen && (

            <div
              style={{
                position: "absolute",
                top: "calc(100% + 10px)",
                right: 0,
                width: 300,
                background:
                  "var(--surface, #fff)",
                border:
                  "1px solid var(--border, #e5e7eb)",
                borderRadius: 10,
                boxShadow:
                  "0 10px 30px rgba(0,0,0,0.12)",
                zIndex: 1000,
                overflow: "hidden",
              }}
            >

              <div
                style={{
                  padding: "14px 16px",
                  borderBottom:
                    "1px solid var(--border, #e5e7eb)",
                  fontWeight: 600,
                  fontSize: 14,
                }}
              >
                Notifications
              </div>


              {loadingNotifications ? (

                <div
                  style={{
                    padding: 16,
                    fontSize: 13,
                    color:
                      "var(--text-tertiary)",
                  }}
                >
                  Loading...
                </div>

              ) : notificationCount === 0 ? (

                <div
                  style={{
                    padding: 20,
                    fontSize: 13,
                    color:
                      "var(--text-tertiary)",
                    textAlign: "center",
                  }}
                >
                  You're all caught up.
                </div>

              ) : (

                <>

                  {/* Pending */}

                  {pendingCount > 0 && (

                    <button
                      type="button"
                      onClick={
                        handlePendingLeads
                      }
                      style={{
                        width: "100%",
                        padding:
                          "14px 16px",
                        border: "none",
                        background:
                          "transparent",
                        textAlign: "left",
                        cursor: "pointer",
                        borderBottom:
                          "1px solid var(--border, #e5e7eb)",
                      }}
                    >

                      <div
                        style={{
                          fontWeight: 600,
                          fontSize: 13,
                        }}
                      >
                        {pendingCount}{" "}
                        {pendingCount === 1
                          ? "email"
                          : "emails"}{" "}
                        awaiting approval
                      </div>

                      <div
                        style={{
                          marginTop: 4,
                          fontSize: 12,
                          color:
                            "var(--text-tertiary)",
                        }}
                      >
                        Review pending
                        emails
                      </div>

                    </button>

                  )}


                  {/* Failed */}

                  {failedCount > 0 && (

                    <button
                      type="button"
                      onClick={
                        handlePendingLeads
                      }
                      style={{
                        width: "100%",
                        padding:
                          "14px 16px",
                        border: "none",
                        background:
                          "transparent",
                        textAlign: "left",
                        cursor: "pointer",
                      }}
                    >

                      <div
                        style={{
                          fontWeight: 600,
                          fontSize: 13,
                        }}
                      >
                        {failedCount}{" "}
                        {failedCount === 1
                          ? "lead"
                          : "leads"}{" "}
                        failed processing
                      </div>

                      <div
                        style={{
                          marginTop: 4,
                          fontSize: 12,
                          color:
                            "var(--text-tertiary)",
                        }}
                      >
                        Review failed
                        leads
                      </div>

                    </button>

                  )}

                </>

              )}

            </div>

          )}

        </div>


        {/* ================================================= */}
        {/* Account                                          */}
        {/* ================================================= */}

        <div
          ref={accountRef}
          style={{
            position: "relative",
          }}
        >

          <button
            className="icon-btn"
            aria-label="Account menu"
            aria-expanded={
              accountOpen
            }
            onClick={
              handleAccountClick
            }
          >
            <CircleUserRound size={22} />
          </button>


          {/* --------------------------------------------- */}
          {/* Account dropdown                              */}
          {/* --------------------------------------------- */}

          {accountOpen && (

            <div
              style={{
                position: "absolute",
                top: "calc(100% + 10px)",
                right: 0,
                width: 190,
                background:
                  "var(--surface, #fff)",
                border:
                  "1px solid var(--border, #e5e7eb)",
                borderRadius: 10,
                boxShadow:
                  "0 10px 30px rgba(0,0,0,0.12)",
                zIndex: 1000,
                overflow: "hidden",
              }}
            >

              <button
                type="button"
                onClick={
                  handleSettings
                }
                style={{
                  width: "100%",
                  padding:
                    "12px 16px",
                  border: "none",
                  background:
                    "transparent",
                  textAlign: "left",
                  cursor: "pointer",
                  fontSize: 13,
                }}
              >
                Settings
              </button>


              <button
                type="button"
                onClick={
                  handleSignOut
                }
                style={{
                  width: "100%",
                  padding:
                    "12px 16px",
                  border: "none",
                  borderTop:
                    "1px solid var(--border, #e5e7eb)",
                  background:
                    "transparent",
                  textAlign: "left",
                  cursor: "pointer",
                  fontSize: 13,
                }}
              >
                Sign out
              </button>

            </div>

          )}

        </div>

      </div>

    </header>
  );
}