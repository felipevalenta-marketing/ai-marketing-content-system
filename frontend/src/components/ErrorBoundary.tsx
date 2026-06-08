import { Component, type ErrorInfo, type ReactNode } from "react";
import { Button } from "./Button";
import { Card } from "./Card";
import { EmptyState } from "./EmptyState";

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  message: string;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, message: "" };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return {
      hasError: true,
      message: error?.message || "An unexpected error occurred while rendering the app.",
    };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    if (typeof import.meta !== "undefined" && import.meta.env?.DEV) {
      console.error("[ui] runtime error", { message: error?.message, stack: error?.stack, componentStack: info?.componentStack });
    }
  }

  handleReset = () => {
    this.setState({ hasError: false, message: "" });
  };

  render() {
    if (this.state.hasError) {
      return (
        <Card>
          <EmptyState
            title="Something went wrong"
            description={this.state.message || "The interface hit an unexpected error. You can retry or go back to the dashboard."}
            action={
              <Button type="button" variant="primary" onClick={this.handleReset}>
                Try again
              </Button>
            }
          />
        </Card>
      );
    }

    return this.props.children;
  }
}
