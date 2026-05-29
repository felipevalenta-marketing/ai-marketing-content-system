import { type ReactNode, useEffect } from "react";
import { Button } from "./Button";
import { Card } from "./Card";
import { EmptyState } from "./EmptyState";
import { LoadingState } from "./LoadingState";

interface AuthGuardProps {
  isAuthenticated: boolean;
  loading: boolean;
  onGoLogin: () => void;
  children: ReactNode;
}

export function AuthGuard({ isAuthenticated, loading, onGoLogin, children }: AuthGuardProps) {
  useEffect(() => {
    if (!loading && !isAuthenticated) {
      onGoLogin();
    }
  }, [isAuthenticated, loading, onGoLogin]);

  if (loading) {
    return <LoadingState label="Checking authentication..." />;
  }

  if (!isAuthenticated) {
    return (
      <Card>
        <EmptyState
          title="Authentication required"
          description="Please log in to access the platform."
          action={
            <Button type="button" variant="primary" onClick={onGoLogin}>
              Go to Login
            </Button>
          }
        />
      </Card>
    );
  }

  return <>{children}</>;
}
