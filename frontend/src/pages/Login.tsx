import { FormEvent, useEffect, useState } from "react";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { SectionHeader } from "../components/SectionHeader";
import { useAuth } from "../hooks/useAuth";
import type { ApiClient } from "../api/client";

interface LoginProps {
  client: ApiClient;
  auth: ReturnType<typeof useAuth>;
  onNavigate: (page: string) => void;
}

export function Login({ auth, onNavigate }: LoginProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  useEffect(() => {
    if (auth.isAuthenticated) {
      onNavigate("dashboard");
    }
  }, [auth.isAuthenticated, onNavigate]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const result = await auth.login({ email, password });
    if (result?.access_token) {
      onNavigate("dashboard");
    }
  };

  return (
    <Card>
      <SectionHeader title="Login" description="Access the platform with your account." />
      <form className="stack" onSubmit={handleSubmit}>
        <label className="field">
          <span>Email</span>
          <input className="input" value={email} onChange={(event) => setEmail(event.target.value)} />
        </label>
        <label className="field">
          <span>Password</span>
          <input className="input" type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
        </label>
        {auth.error ? <p className="error-text">{auth.error}</p> : null}
        <div className="button-row">
          <Button type="submit" variant="primary">
            Login
          </Button>
          <Button type="button" variant="secondary" onClick={() => onNavigate("register")}>
            Create account
          </Button>
        </div>
      </form>
    </Card>
  );
}
