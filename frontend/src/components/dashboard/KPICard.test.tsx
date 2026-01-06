/**
 * KPICard Component Snapshot Tests
 *
 * 测试 KPICard 组件的渲染和快照一致性
 */
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { KPICard } from './KPICard'

describe('KPICard Component', () => {
  it('renders with positive value correctly', () => {
    const { container } = render(
      <KPICard
        title="总盈亏"
        value="$12,345.67"
        trend="up"
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders with negative value correctly', () => {
    const { container } = render(
      <KPICard
        title="今日盈亏"
        value="-$1,234.56"
        trend="down"
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders with percentage value correctly', () => {
    const { container } = render(
      <KPICard
        title="胜率"
        value="68.5%"
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders with integer value correctly', () => {
    const { container } = render(
      <KPICard
        title="交易次数"
        value={150}
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders with subtitle correctly', () => {
    const { container } = render(
      <KPICard
        title="加载中"
        value="--"
        subtitle="Loading..."
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('displays title correctly', () => {
    render(
      <KPICard
        title="Test Title"
        value={100}
      />
    )
    expect(screen.getByText('Test Title')).toBeInTheDocument()
  })

  it('displays currency value correctly', () => {
    render(
      <KPICard
        title="Currency"
        value="$1,234.56"
        trend="up"
      />
    )
    expect(screen.getByText(/1,234/)).toBeInTheDocument()
  })
})
