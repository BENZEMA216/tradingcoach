import { ResponsiveContainer, type ResponsiveContainerProps } from 'recharts';

const INITIAL_DIMENSION = { width: 0, height: 200 };

export function StableResponsiveContainer({
  minWidth = 0,
  minHeight = 200,
  initialDimension = INITIAL_DIMENSION,
  ...props
}: ResponsiveContainerProps) {
  return (
    <ResponsiveContainer
      minWidth={minWidth}
      minHeight={minHeight}
      initialDimension={initialDimension}
      {...props}
    />
  );
}
