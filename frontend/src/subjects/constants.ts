import type { Subject } from "../api/types";

export const UNSORTED_SUBJECT_ID = 0;

export const DEFAULT_UNSORTED_LABEL = "Unsorted";

export function buildUnsortedSubject(label: string): Subject {
  return {
    id: UNSORTED_SUBJECT_ID,
    name: label,
  };
}

export function isUnsortedSubjectId(subjectId: number | null | undefined): boolean {
  return subjectId === UNSORTED_SUBJECT_ID || subjectId === null;
}

export function subjectIdForApi(subjectId: number | null): number | null {
  if (isUnsortedSubjectId(subjectId)) {
    return null;
  }
  return subjectId;
}

export function taskSubjectIdForSelect(taskSubjectId: number | null): number {
  return taskSubjectId ?? UNSORTED_SUBJECT_ID;
}

export function buildSidebarSubjects(
  subjects: Subject[],
  unsortedLabel: string,
  unsortedPosition: number,
): Subject[] {
  const realSubjects = subjects.filter((subject) => subject.id !== UNSORTED_SUBJECT_ID);
  const unsorted = buildUnsortedSubject(unsortedLabel);
  const position = Math.min(Math.max(unsortedPosition, 0), realSubjects.length);
  const result = [...realSubjects];
  result.splice(position, 0, unsorted);
  return result;
}
