import type { ReactNode } from "react";

interface PermissionGateProps {
  permission?: string;
  anyOf?: string[];
  allOf?: string[];
  permissions?: string[];
  role?: string;
  fallback?: ReactNode;
  children: ReactNode;
}

function hasPermission(permissions: string[], permission: string): boolean {
  return permissions.includes("admin:all") || permissions.includes(permission);
}

export function PermissionGate({ permission, anyOf, allOf, permissions = [], fallback = null, children }: PermissionGateProps) {
  const allowed = (() => {
    if (permissions.includes("admin:all")) {
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

  if (!allowed) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}
