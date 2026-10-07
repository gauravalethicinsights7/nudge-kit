import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../state/AuthContext";
import { ApiError } from "../api/client";
import { Card } from "../components/shared/ui";

export function Signup() {
  const { signup } = useAuth();
  const navigate = useNavigate();
  const [tenantName, setTenantName] = useState("");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await signup(tenantName, name, email, password);
      navigate("/");
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Signup failed");
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
      <div style={{ width: 440 }}>
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
          <div className="wordmark" style={{ color: "#fff", fontSize: 24, display: "block" }}>
            NUDGE Omnichannel
          </div>
        </div>

        <Card style={{ margin: 0, boxShadow: "var(--shadow-lg)" }}>
          <h2 style={{ marginBottom: 4 }}>Create a workspace</h2>
          <p style={{ color: "var(--text-3)", fontSize: 12.5, marginBottom: 18 }}>
            This creates a new tenant and makes you its platform admin. Invite teammates afterwards from the Admin console.
          </p>
          <form onSubmit={onSubmit}>
            <div className="grid grid-2">
              <div className="form-row" style={{ maxWidth: "none" }}>
                <label>Organization name</label>
                <input required value={tenantName} onChange={(e) => setTenantName(e.target.value)} style={{ width: "100%" }} />
              </div>
              <div className="form-row" style={{ maxWidth: "none" }}>
                <label>Your name</label>
                <input required value={name} onChange={(e) => setName(e.target.value)} style={{ width: "100%" }} />
              </div>
            </div>
            <div className="form-row" style={{ maxWidth: "none" }}>
              <label>Email</label>
              <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} style={{ width: "100%" }} />
            </div>
            <div className="form-row" style={{ maxWidth: "none" }}>
              <label>Password</label>
              <input type="password" required minLength={8} value={password} onChange={(e) => setPassword(e.target.value)} style={{ width: "100%" }} />
            </div>
            {error && <div className="banner banner-error" style={{ marginBottom: 12 }}>{error}</div>}
            <button className="btn-gold" type="submit" disabled={isSubmitting} style={{ width: "100%" }}>
              {isSubmitting ? "Creating…" : "Create workspace"}
            </button>
          </form>
        </Card>

        <p style={{ fontSize: 12.5, marginTop: 18, textAlign: "center", color: "rgba(255,255,255,0.7)" }}>
          Already have an account?{" "}
          <Link to="/login" style={{ color: "var(--gold-bright)", fontWeight: 600 }}>
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
