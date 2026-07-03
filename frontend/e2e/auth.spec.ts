import { test, expect } from "@playwright/test";

// ── Auth Flow ─────────────────────────────────────────────────────────────────

test.describe("Authentication", () => {
  test("login page renders correctly", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByText("Welcome back")).toBeVisible();
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/password/i)).toBeVisible();
    await expect(page.getByRole("button", { name: /sign in/i })).toBeVisible();
  });

  test("register page renders correctly", async ({ page }) => {
    await page.goto("/register");
    await expect(page.getByText("Create your account")).toBeVisible();
    await expect(page.getByLabel(/full name/i)).toBeVisible();
    await expect(
      page.getByRole("button", { name: /create account/i }),
    ).toBeVisible();
  });

  test("forgot password page renders correctly", async ({ page }) => {
    await page.goto("/forgot-password");
    await expect(page.getByText("Reset your password")).toBeVisible();
    await expect(page.getByLabel(/email/i)).toBeVisible();
  });

  test("unauthenticated user redirected from /chat to /login", async ({
    page,
  }) => {
    await page.goto("/chat");
    await page.waitForURL("**/login", { timeout: 5000 });
    await expect(page.url()).toContain("/login");
  });

  test("invalid login shows error", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel(/email/i).fill("wrong@test.com");
    await page.getByLabel(/password/i).fill("wrongpassword");
    await page.getByRole("button", { name: /sign in/i }).click();
    // Should stay on login page
    await page.waitForTimeout(1500);
    await expect(page.url()).toContain("/login");
  });
});

// ── Navigation ────────────────────────────────────────────────────────────────

test.describe("Public Routes", () => {
  test("root redirects to login when unauthenticated", async ({ page }) => {
    await page.goto("/");
    await page.waitForURL("**/login", { timeout: 5000 });
    await expect(page.url()).toContain("/login");
  });

  test("login page has link to register", async ({ page }) => {
    await page.goto("/login");
    const registerLink = page.getByRole("link", { name: /sign up/i });
    await expect(registerLink).toBeVisible();
    await registerLink.click();
    await expect(page.url()).toContain("/register");
  });

  test("login page has forgot password link", async ({ page }) => {
    await page.goto("/login");
    const forgotLink = page.getByRole("link", { name: /forgot password/i });
    await expect(forgotLink).toBeVisible();
    await forgotLink.click();
    await expect(page.url()).toContain("/forgot-password");
  });

  test("register page has link back to login", async ({ page }) => {
    await page.goto("/register");
    const loginLink = page.getByRole("link", { name: /sign in/i });
    await expect(loginLink).toBeVisible();
  });
});

// ── Authenticated Flow (requires running backend) ─────────────────────────────

test.describe("Authenticated Flow", () => {
  const testUser = {
    email: `e2e_${Date.now()}@techmart-test.com`,
    password: "E2eTest1234!",
    name: "E2E Test User",
  };

  test.skip(
    !process.env.BACKEND_AVAILABLE,
    "Skipped — set BACKEND_AVAILABLE=1 to run authenticated tests",
  );

  test("can register and land on /chat", async ({ page }) => {
    await page.goto("/register");
    await page.getByLabel(/full name/i).fill(testUser.name);
    await page.getByLabel(/email/i).fill(testUser.email);
    await page.getByLabel(/^password$/i).fill(testUser.password);
    await page.getByLabel(/confirm password/i).fill(testUser.password);
    await page.getByRole("button", { name: /create account/i }).click();
    await page.waitForURL("**/chat", { timeout: 10000 });
    await expect(page.url()).toContain("/chat");
  });

  test("can login and see chat interface", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel(/email/i).fill(testUser.email);
    await page.getByLabel(/password/i).fill(testUser.password);
    await page.getByRole("button", { name: /sign in/i }).click();
    await page.waitForURL("**/chat", { timeout: 10000 });
    await expect(
      page.getByRole("log", { name: /conversation/i }),
    ).toBeVisible();
  });

  test("sidebar shows navigation links", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel(/email/i).fill(testUser.email);
    await page.getByLabel(/password/i).fill(testUser.password);
    await page.getByRole("button", { name: /sign in/i }).click();
    await page.waitForURL("**/chat");
    await expect(page.getByRole("link", { name: /history/i })).toBeVisible();
    await expect(page.getByRole("link", { name: /analytics/i })).toBeVisible();
    await expect(page.getByRole("link", { name: /tickets/i })).toBeVisible();
  });

  test("send message triggers agent response", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel(/email/i).fill(testUser.email);
    await page.getByLabel(/password/i).fill(testUser.password);
    await page.getByRole("button", { name: /sign in/i }).click();
    await page.waitForURL("**/chat");

    const input = page.getByRole("textbox", { name: /message input/i });
    await input.fill("What is your refund policy?");
    await page.getByRole("button", { name: /send/i }).click();

    // Wait for assistant response (up to 15s for LLM)
    await expect(
      page.locator('[role="list"] [role="listitem"]').nth(1),
    ).toBeVisible({ timeout: 15000 });
  });
});
