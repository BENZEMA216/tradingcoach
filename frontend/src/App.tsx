import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from '@/components/layout/Layout';
import { ToastContainer } from '@/components/common/Toast';
import { FeedbackButton } from '@/components/feedback/FeedbackButton';
import { LandingUpload } from '@/pages/LandingUpload';
import { Upload } from '@/pages/Upload';
import { AnalysisLoading } from '@/pages/AnalysisLoading';
import { Dashboard } from '@/pages/Dashboard';
import { Positions } from '@/pages/Positions';
import { PositionDetail } from '@/pages/PositionDetail';
import { Statistics } from '@/pages/Statistics';
import { System } from '@/pages/System';
import { AICoach } from '@/pages/AICoach';
import { TaskStatus } from '@/pages/TaskStatus';
import { EventAnalysis } from '@/pages/EventAnalysis';
import { Backtest } from '@/pages/Backtest';

function App() {
  return (
    <BrowserRouter>
      <ToastContainer />
      <FeedbackButton />
      <Routes>
        {/* Landing Page - No Layout */}
        <Route path="/" element={<LandingUpload />} />

        {/* Analysis Loading Page - No Layout */}
        <Route path="/analysis/:taskId" element={<AnalysisLoading />} />

        {/* Main App with Layout */}
        <Route element={<Layout />}>
          <Route path="statistics" element={<Statistics />} />
          <Route path="positions" element={<Positions />} />
          <Route path="positions/:id" element={<PositionDetail />} />
          <Route path="events" element={<EventAnalysis />} />
          <Route path="backtest" element={<Backtest />} />
          <Route path="tasks/:taskId" element={<TaskStatus />} />

          {/* Hidden routes (accessible via URL but not in nav) */}
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="ai-coach" element={<AICoach />} />
          <Route path="upload" element={<Upload />} />
          <Route path="system" element={<System />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
