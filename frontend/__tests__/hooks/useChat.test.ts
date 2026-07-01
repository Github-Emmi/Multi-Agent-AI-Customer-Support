import { renderHook, act } from "@testing-library/react";
import { useChat } from "@/hooks/useChat";
import api from "@/services/api";

// Mock axios
jest.mock("@/services/api", () => ({
  __esModule: true,
  default: {
    post: jest.fn(),
    get: jest.fn(),
  },
}));

const mockApi = api as jest.Mocked<typeof api>;

describe("useChat", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockApi.get.mockResolvedValue({ data: { turns: [] } });
  });

  it("initializes with empty messages", () => {
    const { result } = renderHook(() => useChat());
    expect(result.current.messages).toHaveLength(0);
    expect(result.current.isLoading).toBe(false);
  });

  it("generates a session ID on init", () => {
    const { result } = renderHook(() => useChat());
    expect(result.current.sessionId).toMatch(/^sess_/);
  });

  it("uses provided session ID", () => {
    const { result } = renderHook(() => useChat("sess_abc123"));
    expect(result.current.sessionId).toBe("sess_abc123");
  });

  it("adds user message immediately on send", async () => {
    mockApi.post.mockResolvedValueOnce({
      data: {
        response: "Here is your answer.",
        agents_used: ["faq"],
        session_id: "sess_test",
        response_time_ms: 500,
      },
    });

    const { result } = renderHook(() => useChat());
    await act(async () => {
      await result.current.sendMessage("What are your hours?");
    });

    expect(result.current.messages[0].role).toBe("user");
    expect(result.current.messages[0].content).toBe("What are your hours?");
  });

  it("adds assistant response after send", async () => {
    mockApi.post.mockResolvedValueOnce({
      data: {
        response: "We are open 24/7.",
        agents_used: ["faq"],
        session_id: "sess_test",
        response_time_ms: 800,
      },
    });

    const { result } = renderHook(() => useChat());
    await act(async () => {
      await result.current.sendMessage("What are your hours?");
    });

    expect(result.current.messages).toHaveLength(2);
    expect(result.current.messages[1].role).toBe("assistant");
    expect(result.current.messages[1].content).toBe("We are open 24/7.");
    expect(result.current.messages[1].agents_used).toEqual(["faq"]);
  });

  it("removes user message on API failure", async () => {
    mockApi.post.mockRejectedValueOnce(new Error("Network error"));

    const { result } = renderHook(() => useChat());
    await act(async () => {
      await result.current.sendMessage("What are your hours?");
    });

    expect(result.current.messages).toHaveLength(0);
  });

  it("ignores empty or whitespace-only messages", async () => {
    const { result } = renderHook(() => useChat());
    await act(async () => {
      await result.current.sendMessage("   ");
    });

    expect(mockApi.post).not.toHaveBeenCalled();
    expect(result.current.messages).toHaveLength(0);
  });

  it("resets session correctly", () => {
    const { result } = renderHook(() => useChat());
    const originalId = result.current.sessionId;
    act(() => { result.current.resetSession(); });
    expect(result.current.sessionId).not.toBe(originalId);
    expect(result.current.messages).toHaveLength(0);
  });

  it("sets isLoading during API call", async () => {
    let resolvePost!: (v: unknown) => void;
    mockApi.post.mockReturnValueOnce(
      new Promise((res) => { resolvePost = res; }) as ReturnType<typeof mockApi.post>
    );

    const { result } = renderHook(() => useChat());
    act(() => { result.current.sendMessage("Test"); });
    expect(result.current.isLoading).toBe(true);

    await act(async () => {
      resolvePost({
        data: { response: "OK", agents_used: [], session_id: "x", response_time_ms: 100 },
      });
    });
    expect(result.current.isLoading).toBe(false);
  });
});
