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

export interface Task {
  id: number;
  title: string;
  completed: boolean;
  position: number;
  subject_id: number | null;
}

export interface Subtask {
  id: number;
  title: string;
  completed: boolean;
  task_id: number;
}

export interface TaskFilters {
  completed?: boolean;
  subject_id?: number;
}
