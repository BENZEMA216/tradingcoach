/**
 * AnalysisLoading - 独立分析加载页面
 *
 * input: taskId URL参数
 * output: 展示分析进度，完成后跳转
 * pos: 页面组件 - 全屏两栏布局的loading体验
 */
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { taskApi } from '@/api/client';
import { BrandSection } from '@/components/loading/BrandSection';
import { ProgressPanel } from '@/components/loading/ProgressPanel';
import { BackgroundEffects } from '@/components/landing/BackgroundEffects';

export function AnalysisLoading() {
  const { taskId } = useParams<{ taskId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { t } = useTranslation();

  // Task status polling
  const { data: task, isLoading, error } = useQuery({
    queryKey: ['task', taskId],
    queryFn: () => taskApi.getStatus(taskId!),
    enabled: !!taskId,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data) return 500;
      if (data.status === 'completed' || data.status === 'failed' || data.status === 'cancelled') {
        return false;
      }
      return 500; // 快速轮询
    },
  });

  // Handle completion
  const handleComplete = () => {
    queryClient.invalidateQueries({ queryKey: ['positions'] });
    queryClient.invalidateQueries({ queryKey: ['statistics'] });
    queryClient.invalidateQueries({ queryKey: ['system'] });
  };

  // Handle navigation
  const handleViewPositions = () => {
    navigate('/positions');
  };

  const handleViewDashboard = () => {
    navigate('/statistics');
  };

  const handleRetry = () => {
    navigate('/');
  };

  if (!taskId) {
    navigate('/');
    return null;
  }

  return (
    <div className="min-h-screen bg-black text-white flex relative overflow-hidden font-sans selection:bg-white selection:text-black">
      {/* Background Effects */}
      <BackgroundEffects />

      {/* Left Side - Brand Section (40%) */}
      <div className="w-2/5 min-h-screen flex items-center justify-center relative z-10 border-r border-white/5">
        <BrandSection status={task?.status} />
      </div>

      {/* Right Side - Progress Panel (60%) */}
      <div className="w-3/5 min-h-screen flex items-center justify-center p-8 relative z-10">
        <ProgressPanel
          task={task}
          isLoading={isLoading}
          error={error}
          onComplete={handleComplete}
          onViewPositions={handleViewPositions}
          onViewDashboard={handleViewDashboard}
          onRetry={handleRetry}
        />
      </div>
    </div>
  );
}
