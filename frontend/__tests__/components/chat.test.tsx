import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MessageInput } from "@/components/chat/MessageInput";
import { ChatWindow } from "@/components/chat/ChatWindow";
import type { Message } from "@/types";

// ── MessageInput ──────────────────────────────────────────────────────────

describe("MessageInput", () => {
  it("renders textarea and send button", () => {
    render(<MessageInput onSend={jest.fn()} isLoading={false} />);
    expect(screen.getByRole("textbox", { name: /message input/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /send message/i })).toBeInTheDocument();
  });

  it("send button is disabled when input is empty", () => {
    render(<MessageInput onSend={jest.fn()} isLoading={false} />);
    expect(screen.getByRole("button", { name: /send/i })).toBeDisabled();
  });

  it("enables send button when text is entered", async () => {
    render(<MessageInput onSend={jest.fn()} isLoading={false} />);
    await userEvent.type(screen.getByRole("textbox"), "Hello");
    expect(screen.getByRole("button", { name: /send/i })).toBeEnabled();
  });

  it("calls onSend with trimmed text and clears input", async () => {
    const onSend = jest.fn();
    render(<MessageInput onSend={onSend} isLoading={false} />);
    const textarea = screen.getByRole("textbox");
    await userEvent.type(textarea, "  What is the refund policy?  ");
    await userEvent.click(screen.getByRole("button", { name: /send/i }));
    expect(onSend).toHaveBeenCalledWith("What is the refund policy?");
    expect(textarea).toHaveValue("");
  });

  it("submits on Enter key (not Shift+Enter)", async () => {
    const onSend = jest.fn();
    render(<MessageInput onSend={onSend} isLoading={false} />);
    const textarea = screen.getByRole("textbox");
    await userEvent.type(textarea, "Test message{Enter}");
    expect(onSend).toHaveBeenCalledWith("Test message");
  });

  it("does NOT submit on Shift+Enter", async () => {
    const onSend = jest.fn();
    render(<MessageInput onSend={onSend} isLoading={false} />);
    const textarea = screen.getByRole("textbox");
    await userEvent.type(textarea, "Line 1{shift>}{enter}{/shift}Line 2");
    expect(onSend).not.toHaveBeenCalled();
  });

  it("is disabled while loading", () => {
    render(<MessageInput onSend={jest.fn()} isLoading={true} />);
    expect(screen.getByRole("textbox")).toBeDisabled();
    expect(screen.getByRole("button", { name: /send/i })).toBeDisabled();
  });
});

// ── ChatWindow ────────────────────────────────────────────────────────────

describe("ChatWindow", () => {
  const messages: Message[] = [
    {
      role: "user",
      content: "What is your refund policy?",
      timestamp: new Date().toISOString(),
    },
    {
      role: "assistant",
      content: "You can return items within 30 days.",
      timestamp: new Date().toISOString(),
      agents_used: ["billing"],
    },
  ];

  it("shows welcome screen when no messages", () => {
    render(<ChatWindow messages={[]} isLoading={false} />);
    expect(screen.getByText("Welcome to TechMart Support")).toBeInTheDocument();
  });

  it("renders all messages", () => {
    render(<ChatWindow messages={messages} isLoading={false} />);
    expect(screen.getByText("What is your refund policy?")).toBeInTheDocument();
    expect(screen.getByText(/return items within 30 days/i)).toBeInTheDocument();
  });

  it("shows typing indicator when loading", () => {
    render(<ChatWindow messages={messages} isLoading={true} />);
    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("does not show typing indicator when not loading", () => {
    render(<ChatWindow messages={messages} isLoading={false} />);
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });

  it("has correct log role for accessibility", () => {
    render(<ChatWindow messages={messages} isLoading={false} />);
    expect(screen.getByRole("log")).toBeInTheDocument();
  });

  it("has aria-live on message container", () => {
    render(<ChatWindow messages={messages} isLoading={false} />);
    expect(screen.getByRole("log")).toHaveAttribute("aria-live", "polite");
  });
});
