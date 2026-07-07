export interface User {
  id: number;
  username: string;
  unsorted_label: string;
  unsorted_position: number;
}

export interface Token {
  access_token: string;
  token_type: string;
}

export interface Subject {
  id: number;
  name: string;
}

export type TaskPriority = "low" | "medium" | "high";

export interface Task {
  id: number;
  title: string;
  description: string | null;
  priority: TaskPriority;
  due_date: string | null;
  completed: boolean;
  position: number;
  subject_id: number | null;
}

export interface TaskCreateInput {
  title: string;
  subject_id: number | null;
  description?: string | null;
  priority?: TaskPriority;
  due_date?: string | null;
}

export interface TaskUpdateInput {
  title: string;
  description: string | null;
  priority: TaskPriority;
  due_date: string | null;
  completed: boolean;
  subject_id: number | null;
}

export interface TaskFilters {
  completed?: boolean;
  subject_id?: number;
}
