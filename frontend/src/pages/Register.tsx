import { FormEvent, useEffect, useState } from "react";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { SectionHeader } from "../components/SectionHeader";
import { useAuth } from "../hooks/useAuth";
import type { ApiClient } from "../api/client";

interface RegisterProps {
  client: ApiClient;
  auth: ReturnType<typeof useAuth>;
  onNavigate: (page: string) => void;
}

export function Register({ auth, onNavigate }: RegisterProps) {
  const [email, setEmail] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");

  useEffect(() => {
    if (auth.isAuthenticated) {
      onNavigate("dashboard");
    }
  }, [auth.isAuthenticated, onNavigate]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const result = await auth.register({ email, password, display_name: displayName });
    if (result?.access_token) {
      onNavigate("dashboard");
    }
  };

  return (
    <Card>
      <SectionHeader title="Register" description="Create a new account to access the platform." />
      <form className="stack" onSubmit={handleSubmit}>
        <label className="field">
          <span>Email</span>
          <input className="input" value={email} onChange={(event) => setEmail(event.target.value)} />
        </label>
        <label className="field">
          <span>Display name</span>
          <input className="input" value={displayName} onChange={(event) => setDisplayName(event.target.value)} />
        </label>
        <label className="field">
          <span>Password</span>
          <input className="input" type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
        </label>
        {auth.error ? <p className="error-text">{auth.error}</p> : null}
        <div className="button-row">
          <Button type="submit" variant="primary">
            Create account
          </Button>
          <Button type="button" variant="secondary" onClick={() => onNavigate("login")}>
            Back to login
          </Button>
        </div>
      </form>
    </Card>
  );
}
