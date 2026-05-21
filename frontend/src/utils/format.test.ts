import { describe, expect, it } from 'vitest';
import { isIncompleteGrade } from './format';

describe('grade formatting helpers', () => {
  it('detects downgraded incomplete grades by question-mark suffix', () => {
    expect(isIncompleteGrade('C+?')).toBe(true);
    expect(isIncompleteGrade('C?')).toBe(true);
    expect(isIncompleteGrade('C-?')).toBe(true);
  });

  it('does not treat complete or missing grades as incomplete', () => {
    expect(isIncompleteGrade('C')).toBe(false);
    expect(isIncompleteGrade('F')).toBe(false);
    expect(isIncompleteGrade(null)).toBe(false);
    expect(isIncompleteGrade(undefined)).toBe(false);
  });
});
