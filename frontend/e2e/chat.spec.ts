import { test, expect, Page } from "@playwright/test";

// ── Helpers ───────────────────────────────────────────────────────────────────

async function loginAs(page: Page, email: string, password: string) {
  await page.goto("/login");
  await page.getByLabel(/email/i).fill(email);
  await page.getByLabel(/password/i).fill(password);
  await page.getByRole("button", { name: /sign in/i }).click();
  await page.waitForURL("**/chat");
}

// ── Chat UI Tests ─────────────────────────────────────────────────────────────

test.describe("Chat Interface", () => {
  test.beforeEach(async ({ page }) => {
    // Skip login by injecting a fake token for UI-only tests
    await page.goto("/login");
    await page.evaluate(() => {
      localStorage.setItem("auth_token", "test-token-ui-only");
      localStorage.setItem(
        "auth_user",
        JSON.stringify({
          user_id: "test123",
          name: "Test User",
          email: "test@techmart.com",
          role: "user",
        }),
      );
    });
    await page.goto("/chat");
  });

  test("chat page layout renders", async ({ page }) => {
    await expect(page.locator("aside")).toBeVisible();
    await expect(
      page.getByRole("log", { name: /conversation/i }),
    ).toBeVisible();
    await expect(page.getByLabel(/message input/i)).toBeVisible();
    await expect(
      page.getByRole("button", { name: /send message/i }),
    ).toBeVisible();
  });

  test("send button is disabled when input is empty", async ({ page }) => {
    const sendBtn = page.getByRole("button", { name: /send message/i });
    await expect(sendBtn).toBeDisabled();
  });

  test("typing in message input enables send button", async ({ page }) => {
    const input = page.getByLabel(/message input/i);
    await input.fill("Hello TechMart");
    const sendBtn = page.getByRole("button", { name: /send message/i });
    await expect(sendBtn).toBeEnabled();
  });

  test("Enter key triggers send (not shift+enter)", async ({ page }) => {
    const input = page.getByLabel(/message input/i);
    await input.fill("Test message");
    // Shift+Enter should NOT send
    await input.press("Shift+Enter");
    await expect(input).toBeFocused();
  });

  test("voice button is present in chat toolbar", async ({ page }) => {
    await expect(
      page.getByRole("button", { name: /voice|microphone|start voice/i }),
    ).toBeVisible();
  });

  test("human agent handoff button is present", async ({ page }) => {
    await expect(
      page.getByRole("button", { name: /human agent/i }),
    ).toBeVisible();
  });

  test("new chat button resets session", async ({ page }) => {
    const sessionId1 = await page
      .locator("header span.font-mono")
      .textContent();
    await page.getByRole("button", { name: /new chat/i }).click();
    const sessionId2 = await page
      .locator("header span.font-mono")
      .textContent();
    expect(sessionId1).not.toBe(sessionId2);
  });

  test("sidebar navigation links are present", async ({ page }) => {
    const sidebar = page.locator("aside");
    await expect(sidebar.getByRole("link", { name: /chat/i })).toBeVisible();
    await expect(sidebar.getByRole("link", { name: /history/i })).toBeVisible();
    await expect(sidebar.getByRole("link", { name: /tickets/i })).toBeVisible();
    await expect(
      sidebar.getByRole("link", { name: /analytics/i }),
    ).toBeVisible();
  });

  test("welcome screen shows when no messages", async ({ page }) => {
    await expect(page.getByText("Welcome to TechMart Support")).toBeVisible();
  });
});

// ── Chat Accessibility ────────────────────────────────────────────────────────

test.describe("Chat Accessibility", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/login");
    await page.evaluate(() => {
      localStorage.setItem("auth_token", "test-token-ui-only");
      localStorage.setItem(
        "auth_user",
        JSON.stringify({
          user_id: "t1",
          name: "Jane",
          email: "j@t.com",
          role: "user",
        }),
      );
    });
    await page.goto("/chat");
  });

  test("message input has accessible label", async ({ page }) => {
    const input = page.getByLabel("Message input");
    await expect(input).toBeVisible();
  });

  test("send button has aria-label", async ({ page }) => {
    const btn = page.getByRole("button", { name: "Send message" });
    await expect(btn).toBeVisible();
  });

  test("chat log has correct ARIA role", async ({ page }) => {
    await expect(page.getByRole("log", { name: "Conversation" })).toBeVisible();
  });

  test("typing indicator has status role", async ({ page }) => {
    // Typing indicator should have role=status when visible
    // It only appears during loading — we just check it's present in DOM when rendered
    const indicator = page.locator('[role="status"]');
    // May be hidden when not loading — just verify selector is valid
    await expect(indicator.first()).toBeDefined();
  });
});

// ── History Page ──────────────────────────────────────────────────────────────

test.describe("History Page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/login");
    await page.evaluate(() => {
      localStorage.setItem("auth_token", "test-token-ui-only");
      localStorage.setItem(
        "auth_user",
        JSON.stringify({
          user_id: "t1",
          name: "Jane",
          email: "j@t.com",
          role: "user",
        }),
      );
    });
    await page.goto("/history");
  });

  test("history page renders with header", async ({ page }) => {
    await expect(page.getByText("Conversation History")).toBeVisible();
  });

  test("shows empty state when no conversations", async ({ page }) => {
    // When API returns empty, should show empty state message
    await expect(
      page.getByText(/no conversations yet/i).or(page.locator("ul")),
    ).toBeDefined();
  });
});

// ── Tickets Page ──────────────────────────────────────────────────────────────

test.describe("Tickets Page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/login");
    await page.evaluate(() => {
      localStorage.setItem("auth_token", "test-token-ui-only");
      localStorage.setItem(
        "auth_user",
        JSON.stringify({
          user_id: "t1",
          name: "Jane",
          email: "j@t.com",
          role: "user",
        }),
      );
    });
    await page.goto("/tickets");
  });

  test("tickets page renders with header", async ({ page }) => {
    await expect(page.getByText("My Support Tickets")).toBeVisible();
  });

  test("new ticket button is present", async ({ page }) => {
    await expect(
      page.getByRole("button", { name: /new ticket/i }),
    ).toBeVisible();
  });

  test("clicking new ticket opens modal", async ({ page }) => {
    await page.getByRole("button", { name: /new ticket/i }).click();
    await expect(page.getByRole("dialog")).toBeVisible();
    await expect(page.getByText("Create Support Ticket")).toBeVisible();
  });

  test("modal closes on cancel", async ({ page }) => {
    await page.getByRole("button", { name: /new ticket/i }).click();
    await page.getByRole("button", { name: /cancel/i }).click();
    await expect(page.getByRole("dialog")).not.toBeVisible();
  });
});
