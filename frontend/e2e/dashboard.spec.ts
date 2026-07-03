import { test, expect, Page } from "@playwright/test";

// ── Helpers ───────────────────────────────────────────────────────────────────

async function injectAuth(page: Page) {
  await page.goto("/login");
  await page.evaluate(() => {
    localStorage.setItem("auth_token", "test-token-ui-only");
    localStorage.setItem(
      "auth_user",
      JSON.stringify({
        user_id: "test123",
        name: "Test Admin",
        email: "admin@techmart.com",
        role: "admin",
      }),
    );
  });
}

// ── Analytics Dashboard ───────────────────────────────────────────────────────

test.describe("Analytics Dashboard", () => {
  test.beforeEach(async ({ page }) => {
    await injectAuth(page);
    await page.goto("/analytics");
  });

  test("analytics page renders", async ({ page }) => {
    await expect(page.getByText("Analytics Dashboard")).toBeVisible();
  });

  test("four KPI stat cards are present", async ({ page }) => {
    await expect(page.getByText("Total Conversations")).toBeVisible();
    await expect(page.getByText("Avg Response Time")).toBeVisible();
    await expect(page.getByText("Satisfaction")).toBeVisible();
    await expect(page.getByText("Open Tickets")).toBeVisible();
  });

  test("refresh button is present and clickable", async ({ page }) => {
    const refreshBtn = page.getByRole("button", { name: /refresh/i });
    await expect(refreshBtn).toBeVisible();
    await refreshBtn.click();
    // Should not throw or navigate
    await expect(page.getByText("Analytics Dashboard")).toBeVisible();
  });

  test("navigation to analytics from sidebar", async ({ page }) => {
    await page.goto("/chat");
    await page.evaluate(() => {
      localStorage.setItem("auth_token", "test-token-ui-only");
      localStorage.setItem(
        "auth_user",
        JSON.stringify({
          user_id: "t1",
          name: "Admin",
          email: "a@t.com",
          role: "admin",
        }),
      );
    });
    await page.goto("/chat");
    await page
      .locator("aside")
      .getByRole("link", { name: /analytics/i })
      .click();
    await page.waitForURL("**/analytics");
    await expect(page.getByText("Analytics Dashboard")).toBeVisible();
  });
});

// ── Admin Panel ───────────────────────────────────────────────────────────────

test.describe("Admin Panel", () => {
  test.beforeEach(async ({ page }) => {
    await injectAuth(page);
    await page.goto("/admin");
  });

  test("admin page renders", async ({ page }) => {
    await expect(page.getByText("Knowledge Base Admin")).toBeVisible();
  });

  test("upload area is present", async ({ page }) => {
    await expect(
      page.getByRole("button", { name: /upload|drop a pdf/i }),
    ).toBeVisible();
  });

  test("re-index all button is present", async ({ page }) => {
    await expect(
      page.getByRole("button", { name: /re-index all/i }),
    ).toBeVisible();
  });

  test("indexed documents section is present", async ({ page }) => {
    await expect(page.getByText(/indexed documents/i)).toBeVisible();
  });
});

// ── Protected Route Redirects ─────────────────────────────────────────────────

test.describe("Protected Routes", () => {
  test("unauthenticated user is redirected from /chat to /login", async ({
    page,
  }) => {
    await page.evaluate(() => {
      localStorage.removeItem("auth_token");
      localStorage.removeItem("auth_user");
    });
    await page.goto("/chat");
    await page.waitForURL("**/login", { timeout: 5000 });
    await expect(page.url()).toContain("/login");
  });

  test("unauthenticated user is redirected from /analytics to /login", async ({
    page,
  }) => {
    await page.evaluate(() => {
      localStorage.removeItem("auth_token");
      localStorage.removeItem("auth_user");
    });
    await page.goto("/analytics");
    await page.waitForURL("**/login", { timeout: 5000 });
    await expect(page.url()).toContain("/login");
  });

  test("/login is accessible without auth", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByText("Welcome back")).toBeVisible();
  });

  test("/register is accessible without auth", async ({ page }) => {
    await page.goto("/register");
    await expect(page.getByText("Create your account")).toBeVisible();
  });

  test("/forgot-password is accessible without auth", async ({ page }) => {
    await page.goto("/forgot-password");
    await expect(page.getByText("Reset your password")).toBeVisible();
  });
});

// ── Forgot Password Flow ──────────────────────────────────────────────────────

test.describe("Forgot Password", () => {
  test("forgot password page renders", async ({ page }) => {
    await page.goto("/forgot-password");
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(
      page.getByRole("button", { name: /send reset link/i }),
    ).toBeVisible();
  });

  test("back to sign in link navigates to login", async ({ page }) => {
    await page.goto("/forgot-password");
    await page.getByRole("link", { name: /sign in/i }).click();
    await page.waitForURL("**/login");
    await expect(page.url()).toContain("/login");
  });

  test("reset password confirm page shows invalid state without token", async ({
    page,
  }) => {
    await page.goto("/reset-password");
    await expect(page.getByText(/expired or invalid/i)).toBeVisible();
  });

  test("reset password confirm page shows form with valid token", async ({
    page,
  }) => {
    await page.goto("/reset-password?token=validtesttoken123");
    await expect(page.getByLabel(/new password/i)).toBeVisible();
    await expect(page.getByLabel(/confirm/i)).toBeVisible();
    await expect(
      page.getByRole("button", { name: /reset password/i }),
    ).toBeVisible();
  });
});

// ── Responsive Layout ─────────────────────────────────────────────────────────

test.describe("Responsive Design", () => {
  test("login page is responsive on mobile", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 }); // iPhone 14
    await page.goto("/login");
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByRole("button", { name: /sign in/i })).toBeVisible();
  });

  test("chat page adapts to tablet viewport", async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 }); // iPad
    await page.evaluate(() => {
      localStorage.setItem("auth_token", "test-token");
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
    await expect(page.getByLabel(/message input/i)).toBeVisible();
  });
});
