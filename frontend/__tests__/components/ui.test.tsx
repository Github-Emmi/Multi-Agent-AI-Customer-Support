import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MessageBubble } from "@/components/chat/MessageBubble";
import { TypingIndicator } from "@/components/chat/TypingIndicator";
import { AgentBadge } from "@/components/chat/AgentBadge";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import type { Message } from "@/types";

// ── MessageBubble ──────────────────────────────────────────────────────────

describe("MessageBubble", () => {
  const userMsg: Message = {
    role: "user",
    content: "How do I get a refund?",
    timestamp: new Date().toISOString(),
  };
  const assistantMsg: Message = {
    role: "assistant",
    content: "Your refund will be processed in 5–7 days.",
    timestamp: new Date().toISOString(),
    agents_used: ["billing"],
    response_time_ms: 1200,
  };

  it("renders user message with correct content", () => {
    render(<MessageBubble message={userMsg} />);
    expect(screen.getByText("How do I get a refund?")).toBeInTheDocument();
  });

  it("user bubble has blue background class", () => {
    const { container } = render(<MessageBubble message={userMsg} />);
    const bubble = container.querySelector(".bg-blue-600");
    expect(bubble).toBeInTheDocument();
  });

  it("renders assistant message with agent badge", () => {
    render(<MessageBubble message={assistantMsg} />);
    expect(screen.getByText("Billing")).toBeInTheDocument();
  });

  it("shows response time for assistant messages", () => {
    render(<MessageBubble message={assistantMsg} />);
    expect(screen.getByText("1.2s")).toBeInTheDocument();
  });

  it("assistant bubble does NOT have blue background", () => {
    const { container } = render(<MessageBubble message={assistantMsg} />);
    const blueBubble = container.querySelector(".bg-blue-600");
    expect(blueBubble).not.toBeInTheDocument();
  });

  it("has correct ARIA role listitem", () => {
    const { container } = render(<MessageBubble message={userMsg} />);
    expect(container.querySelector('[role="listitem"]')).toBeInTheDocument();
  });
});

// ── TypingIndicator ────────────────────────────────────────────────────────

describe("TypingIndicator", () => {
  it("renders three animated dots", () => {
    const { container } = render(<TypingIndicator />);
    const dots = container.querySelectorAll(".animate-bounce-dot");
    expect(dots).toHaveLength(3);
  });

  it("has correct ARIA status role", () => {
    render(<TypingIndicator />);
    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("has accessible sr-only label", () => {
    render(<TypingIndicator />);
    expect(screen.getByText("Assistant is typing...")).toBeInTheDocument();
  });
});

// ── AgentBadge ─────────────────────────────────────────────────────────────

describe("AgentBadge", () => {
  it("renders correct label for billing agent", () => {
    render(<AgentBadge agent="billing" />);
    expect(screen.getByText("Billing")).toBeInTheDocument();
  });

  it("renders correct label for technical agent", () => {
    render(<AgentBadge agent="technical" />);
    expect(screen.getByText("Technical Support")).toBeInTheDocument();
  });

  it("has correct accessible ARIA label", () => {
    render(<AgentBadge agent="product" />);
    expect(screen.getByLabelText("Handled by Product agent")).toBeInTheDocument();
  });

  it("renders unknown agent gracefully", () => {
    render(<AgentBadge agent="unknown_agent" />);
    expect(screen.getByText("unknown_agent")).toBeInTheDocument();
  });
});

// ── Button ─────────────────────────────────────────────────────────────────

describe("Button", () => {
  it("renders children correctly", () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole("button", { name: "Click me" })).toBeInTheDocument();
  });

  it("calls onClick when clicked", async () => {
    const onClick = jest.fn();
    render(<Button onClick={onClick}>Submit</Button>);
    await userEvent.click(screen.getByRole("button"));
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it("is disabled when isLoading=true", () => {
    render(<Button isLoading>Loading</Button>);
    expect(screen.getByRole("button")).toBeDisabled();
  });

  it("is disabled when disabled prop is passed", () => {
    render(<Button disabled>Disabled</Button>);
    expect(screen.getByRole("button")).toBeDisabled();
  });
});

// ── Input ──────────────────────────────────────────────────────────────────

describe("Input", () => {
  it("renders with label", () => {
    render(<Input label="Email address" />);
    expect(screen.getByLabelText("Email address")).toBeInTheDocument();
  });

  it("shows required asterisk", () => {
    render(<Input label="Email" required />);
    expect(screen.getByText("*")).toBeInTheDocument();
  });

  it("renders error message", () => {
    render(<Input label="Email" error="Email is required" />);
    expect(screen.getByRole("alert")).toHaveTextContent("Email is required");
  });

  it("calls onChange when typing", async () => {
    const onChange = jest.fn();
    render(<Input label="Name" onChange={onChange} />);
    await userEvent.type(screen.getByLabelText("Name"), "Jane");
    expect(onChange).toHaveBeenCalled();
  });
});
