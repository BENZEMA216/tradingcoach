import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { GradeBadge } from './GradeBadge';

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, params?: { term?: string; defaultValue?: string }) => {
      const translations: Record<string, string> = {
        'glossary.scoreGradeIncomplete.term': '不完整评分',
        'glossary.scoreGradeIncomplete.fullName': 'Incomplete Grade',
        'glossary.scoreGradeIncomplete.description': '虚线边框和信息图标表示该评分使用的数据不完整。',
      };
      return translations[key] ?? params?.defaultValue ?? key;
    },
  }),
}));

describe('GradeBadge', () => {
  it('shows the base grade and hides the raw incomplete suffix', () => {
    render(<GradeBadge grade="C-?" showIncompleteInfo />);

    expect(screen.getByText('C-')).toBeInTheDocument();
    expect(screen.queryByText('C-?')).not.toBeInTheDocument();
    expect(screen.getByLabelText('Info about 不完整评分')).toBeInTheDocument();
  });
});
