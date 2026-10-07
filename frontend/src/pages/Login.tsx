import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../state/AuthContext";
import { ApiError } from "../api/client";
import { Card } from "../components/shared/ui";

// Pre-filled with a known-working demo account so the demo is one click,
// not a credentials-memorization exercise — this is a local demo instance,
// not a production login.
const DEMO_EMAIL = "gaurav.s@alethicinsights.com";
const DEMO_PASSWORD = "DemoPass123!";

export function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState(DEMO_EMAIL);
  const [password, setPassword] = useState(DEMO_PASSWORD);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await login(email, password);
      navigate("/");
    } catch (err) {
      setError(
        err instanceof ApiError
          ? `${err.detail} — if this keeps failing, the backend API server may be down.`
          : "Could not reach the API server — it may be down.",
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "linear-gradient(160deg, var(--navy) 0%, var(--navy-mid) 55%, var(--navy-light) 100%)",
        padding: 24,
      }}
    >
      <div style={{ width: 400 }}>
        <div style={{ textAlign: "center", marginBottom: 28 }}>
          <div
            style={{
              width: 44,
              height: 44,
              borderRadius: "var(--radius-md)",
              background: "var(--gold)",
              color: "var(--navy)",
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 20,
              fontWeight: 700,
              marginBottom: 14,
              fontFamily: "'Playfair Display', Georgia, serif",
            }}
          >
            N
          </div>
          <div
            className="wordmark"
            style={{ color: "#fff", fontSize: 24, display: "block", marginBottom: 6 }}
          >
            NUDGE Omnichannel
          </div>
          <div
            style={{
              fontSize: 11,
              fontWeight: 700,
              textTransform: "uppercase",
              letterSpacing: "0.12em",
              color: "var(--gold)",
            }}
          >
            Pharma decision engine
          </div>
        </div>

        <Card style={{ margin: 0, boxShadow: "var(--shadow-lg)" }}>
          <h2 style={{ marginBottom: 4 }}>Sign in</h2>
          <p style={{ color: "var(--text-3)", fontSize: 12.5, marginBottom: 18 }}>
            Demo workspace — credentials are pre-filled.
          </p>
          <form onSubmit={onSubmit}>
            <div className="form-row" style={{ maxWidth: "none" }}>
              <label>Email</label>
              <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} style={{ width: "100%" }} />
            </div>
            <div className="form-row" style={{ maxWidth: "none" }}>
              <label>Password</label>
              <input type="password" required value={password} onChange={(e) => setPassword(e.target.value)} style={{ width: "100%" }} />
            </div>
            {error && <div className="banner banner-error" style={{ marginBottom: 12 }}>{error}</div>}
            <button className="btn-gold" type="submit" disabled={isSubmitting} style={{ width: "100%" }}>
              {isSubmitting ? "Signing in…" : "Sign in"}
            </button>
          </form>
        </Card>

        <p style={{ fontSize: 12.5, marginTop: 18, textAlign: "center", color: "rgba(255,255,255,0.7)" }}>
          New organization?{" "}
          <Link to="/signup" style={{ color: "var(--gold-bright)", fontWeight: 600 }}>
            Create a workspace
          </Link>
        </p>
      </div>
    </div>
  );
}
