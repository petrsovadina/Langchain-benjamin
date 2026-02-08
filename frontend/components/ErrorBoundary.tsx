"use client";

import { Component, ReactNode } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  variant?: "default" | "minimal";
  onReset?: () => void;
  className?: string;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("ErrorBoundary caught:", error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: undefined });
    this.props.onReset?.();
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      const { variant = "default", className } = this.props;

      if (variant === "minimal") {
        return (
          <div
            data-slot="error-boundary"
            data-variant="minimal"
            className={cn("p-4 text-center", className)}
            role="alert"
          >
            <AlertCircle className="h-8 w-8 text-destructive mx-auto mb-2" />
            <p className="text-sm text-secondary mb-2">Došlo k chybě</p>
            <Button size="sm" onClick={this.handleReset}>
              Zkusit znovu
            </Button>
          </div>
        );
      }

      return (
        <div
          data-slot="error-boundary"
          data-variant="default"
          className={cn("flex items-center justify-center min-h-screen p-4", className)}
          role="alert"
        >
          <Card className="max-w-md w-full">
            <CardHeader>
              <div className="flex items-center gap-3">
                <AlertCircle className="h-8 w-8 text-destructive shrink-0" />
                <CardTitle>Něco se pokazilo</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-secondary">
                Omlouváme se, došlo k neočekávané chybě. Zkuste prosím obnovit stránku nebo se
                vrátit na hlavní stránku.
              </p>
              {process.env.NODE_ENV === "development" && this.state.error && (
                <details className="mt-4 p-3 bg-surface-muted rounded-md text-xs">
                  <summary className="cursor-pointer font-medium">Technické detaily</summary>
                  <pre className="mt-2 overflow-auto">{this.state.error.message}</pre>
                </details>
              )}
            </CardContent>
            <CardFooter className="flex gap-2">
              <Button onClick={this.handleReset} className="flex-1">
                Zkusit znovu
              </Button>
              <Button
                variant="outline"
                onClick={() => window.location.reload()}
                className="flex-1"
              >
                Obnovit stránku
              </Button>
            </CardFooter>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}
