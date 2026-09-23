"use client";

import React from "react";

export class ErrorBoundary extends React.Component<
  { children: React.ReactNode; fallback?: React.ReactNode },
  { hasError: boolean }
> {
  state = { hasError: false };
  static getDerivedStateFromError() {
    return { hasError: true };
  }
  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <div style={{ padding: 20, color: "red" }}>Something went wrong.</div>
        )
      );
    }
    return this.props.children;
  }
}
