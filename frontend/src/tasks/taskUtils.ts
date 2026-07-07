import type { TaskUpdateInput } from "../api/types";
import type { Task } from "../api/types";

export function taskToUpdateInput(task: Task): TaskUpdateInput {
  return {
    title: task.title,
    description: task.description,
    priority: task.priority,
    due_date: task.due_date,
    completed: task.completed,
    subject_id: task.subject_id,
  };
}

export function formatDueDate(isoDate: string): string {
  const date = new Date(`${isoDate}T00:00:00`);
  return date.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function isTaskOverdue(task: Task): boolean {
  if (!task.due_date || task.completed) {
    return false;
  }
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const due = new Date(`${task.due_date}T00:00:00`);
  return due < today;
}

export function priorityLabel(priority: Task["priority"]): string {
  return priority.charAt(0).toUpperCase() + priority.slice(1);
}
