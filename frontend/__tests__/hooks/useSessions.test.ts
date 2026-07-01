import { renderHook, act } from "@testing-library/react";
import { useSessions } from "@/hooks/useSessions";
import { useAnalytics } from "@/hooks/useAnalytics";
import api from "@/services/api";

jest.mock("@/services/api", () => ({
  __esModule: true,
  default: { get: jest.fn() },
}));

const mockApi = api as jest.Mocked<typeof api>;

// ── useSessions ───────────────────────────────────────────────────────────

describe("useSessions", () => {
  beforeEach(() => jest.clearAllMocks());

  it("loads sessions on mount", async () => {
    const mockSessions = [
      { session_id: "sess_1", title: "Refund question", is_resolved: false },
      { session_id: "sess_2", title: "Login issue", is_resolved: true },
    ];
    mockApi.get.mockResolvedValueOnce({ data: mockSessions });

    const { result } = renderHook(() => useSessions());
    await act(async () => {});

    expect(result.current.sessions).toHaveLength(2);
    expect(result.current.sessions[0].title).toBe("Refund question");
  });

  it("handles empty sessions gracefully", async () => {
    mockApi.get.mockResolvedValueOnce({ data: [] });
    const { result } = renderHook(() => useSessions());
    await act(async () => {});
    expect(result.current.sessions).toHaveLength(0);
    expect(result.current.isLoading).toBe(false);
  });

  it("does not throw on API error", async () => {
    mockApi.get.mockRejectedValueOnce(new Error("Unauthorized"));
    const { result } = renderHook(() => useSessions());
    await act(async () => {});
    expect(result.current.sessions).toHaveLength(0);
    expect(result.current.isLoading).toBe(false);
  });
});

// ── useAnalytics ──────────────────────────────────────────────────────────

describe("useAnalytics", () => {
  const mockSummary = {
    total_conversations: 42,
    avg_response_time_ms: 1800,
    satisfaction_score: 4.2,
  };
  const mockAgentUsage = [{ agent: "billing", count: 15 }];
  const mockDaily = [{ date: "2026-07-01", count: 5 }];

  beforeEach(() => jest.clearAllMocks());

  it("fetches all analytics data in parallel", async () => {
    mockApi.get
      .mockResolvedValueOnce({ data: mockSummary })
      .mockResolvedValueOnce({ data: mockAgentUsage })
      .mockResolvedValueOnce({ data: mockDaily });

    const { result } = renderHook(() => useAnalytics());
    await act(async () => {});

    expect(result.current.summary?.total_conversations).toBe(42);
    expect(result.current.agentUsage).toHaveLength(1);
    expect(result.current.dailyData).toHaveLength(1);
  });

  it("sets error on fetch failure", async () => {
    mockApi.get.mockRejectedValue(new Error("Server error"));
    const { result } = renderHook(() => useAnalytics());
    await act(async () => {});
    expect(result.current.error).toBe("Failed to load analytics data");
  });

  it("exposes refetch function", async () => {
    mockApi.get
      .mockResolvedValue({ data: mockSummary })
      .mockResolvedValue({ data: [] })
      .mockResolvedValue({ data: [] });

    const { result } = renderHook(() => useAnalytics());
    await act(async () => {});
    await act(async () => { await result.current.refetch(); });
    expect(mockApi.get).toHaveBeenCalledTimes(6); // 3 on mount + 3 on refetch
  });
});
