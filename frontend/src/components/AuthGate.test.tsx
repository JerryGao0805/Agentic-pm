import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AuthGate } from "@/components/AuthGate";
import { initialData } from "@/lib/kanban";

const jsonResponse = (payload: unknown, status = 200) =>
  new Response(JSON.stringify(payload), {
    status,
    headers: { "Content-Type": "application/json" },
  });

describe("AuthGate", () => {
  beforeEach(() => {
    window.localStorage.removeItem("pm-local-authenticated");
    window.localStorage.removeItem("pm-local-board");
    window.localStorage.removeItem("pm-local-chat-history");
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it("shows sign in when session is unauthenticated", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ authenticated: false, username: null }));
    vi.stubGlobal("fetch", fetchMock);

    render(<AuthGate />);

    expect(await screen.findByRole("heading", { name: /sign in/i })).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/auth/session",
      expect.objectContaining({ credentials: "include" })
    );
  });

  it("logs in successfully and shows board controls", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ authenticated: false, username: null }))
      .mockResolvedValueOnce(jsonResponse({ authenticated: true, username: "user" }))
      .mockResolvedValueOnce(jsonResponse(initialData))
      .mockResolvedValueOnce(jsonResponse([]));
    vi.stubGlobal("fetch", fetchMock);

    render(<AuthGate />);

    await screen.findByRole("heading", { name: /sign in/i });
    await userEvent.type(screen.getByLabelText(/username/i), "user");
    await userEvent.type(screen.getByLabelText(/password/i), "password");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));

    expect(await screen.findByRole("button", { name: /log out/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Kanban Studio" })).toBeInTheDocument();
  });

  it("shows an error for invalid credentials", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ authenticated: false, username: null }))
      .mockResolvedValueOnce(jsonResponse({ detail: "Invalid credentials." }, 401));
    vi.stubGlobal("fetch", fetchMock);

    render(<AuthGate />);

    await screen.findByRole("heading", { name: /sign in/i });
    await userEvent.type(screen.getByLabelText(/username/i), "user");
    await userEvent.type(screen.getByLabelText(/password/i), "wrong");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/invalid credentials/i);
  });

  it("logs out and returns to sign in view", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ authenticated: true, username: "user" }))
      .mockResolvedValueOnce(jsonResponse(initialData))
      .mockResolvedValueOnce(jsonResponse([]))
      .mockResolvedValueOnce(jsonResponse({ authenticated: false, username: null }));
    vi.stubGlobal("fetch", fetchMock);

    render(<AuthGate />);

    await screen.findByRole("button", { name: /log out/i });
    await userEvent.click(screen.getByRole("button", { name: /log out/i }));

    expect(await screen.findByRole("heading", { name: /sign in/i })).toBeInTheDocument();
  });
});
