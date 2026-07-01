import type { Subject, Subtask, Task, TaskFilters, Token, User } from "./types";

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const TOKEN_KEY = "student_task_token";

let unauthorizedHandler: (() => void) | null = null;

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

export function setUnauthorizedHandler(handler: () => void): void {
  unauthorizedHandler = handler;
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  const token = getToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${BASE_URL}${path}`, { ...options, headers });

  if (!response.ok) {
    if (response.status === 401 && token) {
      clearToken();
      unauthorizedHandler?.();
    }

    let detail = response.statusText;
    try {
      const body = await response.json();
      if (typeof body?.detail === "string") {
        detail = body.detail;
      } else if (Array.isArray(body?.detail) && body.detail[0]?.msg) {
        detail = body.detail[0].msg;
      }
    } catch {
      // Response had no JSON body; fall back to the status text.
    }
    throw new ApiError(response.status, detail);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

function jsonRequest<T>(path: string, method: string, body: unknown): Promise<T> {
  return request<T>(path, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export const api = {
  register(username: string, password: string): Promise<User> {
    return jsonRequest<User>("/auth/register", "POST", { username, password });
  },

  async login(username: string, password: string): Promise<Token> {
    const form = new URLSearchParams();
    form.set("username", username);
    form.set("password", password);
    const token = await request<Token>("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: form.toString(),
    });
    return token;
  },

  me(): Promise<User> {
    return request<User>("/auth/me");
  },

  listSubjects(): Promise<Subject[]> {
    return request<Subject[]>("/subjects");
  },

  createSubject(name: string): Promise<Subject> {
    return jsonRequest<Subject>("/subjects", "POST", { name });
  },

  deleteSubject(id: number): Promise<void> {
    return request<void>(`/subjects/${id}`, { method: "DELETE" });
  },

  listTasks(filters: TaskFilters = {}): Promise<Task[]> {
    const params = new URLSearchParams();
    if (filters.completed !== undefined) {
      params.set("completed", String(filters.completed));
    }
    if (filters.q) {
      params.set("q", filters.q);
    }
    if (filters.subject_id !== undefined) {
      params.set("subject_id", String(filters.subject_id));
    }
    const query = params.toString();
    return request<Task[]>(`/tasks${query ? `?${query}` : ""}`);
  },

  createTask(title: string, subjectId: number | null): Promise<Task> {
    return jsonRequest<Task>("/tasks", "POST", {
      title,
      subject_id: subjectId,
    });
  },

  updateTask(
    id: number,
    data: { title: string; completed: boolean; subject_id: number | null },
  ): Promise<Task> {
    return jsonRequest<Task>(`/tasks/${id}`, "PUT", data);
  },

  deleteTask(id: number): Promise<void> {
    return request<void>(`/tasks/${id}`, { method: "DELETE" });
  },

  listSubtasks(taskId: number): Promise<Subtask[]> {
    return request<Subtask[]>(`/tasks/${taskId}/subtasks`);
  },

  createSubtask(taskId: number, title: string): Promise<Subtask> {
    return jsonRequest<Subtask>(`/tasks/${taskId}/subtasks`, "POST", { title });
  },

  updateSubtask(
    taskId: number,
    subtaskId: number,
    data: { title: string; completed: boolean },
  ): Promise<Subtask> {
    return jsonRequest<Subtask>(
      `/tasks/${taskId}/subtasks/${subtaskId}`,
      "PUT",
      data,
    );
  },

  deleteSubtask(taskId: number, subtaskId: number): Promise<void> {
    return request<void>(`/tasks/${taskId}/subtasks/${subtaskId}`, {
      method: "DELETE",
    });
  },
};
