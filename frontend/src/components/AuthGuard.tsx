import { type ReactNode, useEffect } from "react";
import { Button } from "./Button";
import { Card } from "./Card";
import { EmptyState } from "./EmptyState";
import { LoadingState } from "./LoadingState";

interface AuthGuardProps {
  isAuthenticated: boolean;
  loading: boolean;
  permissions?: string[];
  permission?: string;
  anyOf?: string[];
  allOf?: string[];
  onGoLogin: () => void;
  children: ReactNode;
}

function hasPermission(permissions: string[], permission: string): boolean {
  return permissions.includes("admin:all") || permissions.includes(permission);
}

export function AuthGuard({ isAuthenticated, loading, permissions = [], permission, anyOf, allOf, onGoLogin, children }: AuthGuardProps) {
  useEffect(() => {
    if (!loading && !isAuthenticated) {
      onGoLogin();
    }
  }, [isAuthenticated, loading, onGoLogin]);

  const allowed = (() => {
    if (!permission && !anyOf?.length && !allOf?.length) {
      return true;
    }
    if (permission) {
      return hasPermission(permissions, permission);
    }
    if (anyOf?.length) {
      return anyOf.some((item) => hasPermission(permissions, item));
    }
    if (allOf?.length) {
      return allOf.every((item) => hasPermission(permissions, item));
    }
    return true;
  })();

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

  if (!allowed) {
    return (
      <Card>
        <EmptyState title="Access denied" description="Your role does not grant access to this area." />
      </Card>
    );
  }

  return <>{children}</>;
}
