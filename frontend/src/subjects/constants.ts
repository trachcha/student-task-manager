import type { Subject } from "../api/types";

export const UNSORTED_SUBJECT_ID = 0;

export const UNSORTED_SUBJECT: Subject = {
  id: UNSORTED_SUBJECT_ID,
  name: "Unsorted",
};

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

export function withUnsortedSubject(subjects: Subject[]): Subject[] {
  const realSubjects = subjects.filter((subject) => subject.id !== UNSORTED_SUBJECT_ID);
  return [UNSORTED_SUBJECT, ...realSubjects];
}
