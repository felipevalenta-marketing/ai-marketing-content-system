import type { ReactNode } from "react";
import { Card } from "./Card";
import { SectionHeader } from "./SectionHeader";

interface ConfigurationCardProps {
  title: string;
  description?: string;
  children: ReactNode;
}

export function ConfigurationCard({ title, description, children }: ConfigurationCardProps) {
  return (
    <Card>
      <SectionHeader title={title} description={description} />
      {children}
    </Card>
  );
}

