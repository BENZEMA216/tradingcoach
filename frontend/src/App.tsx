import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from '@/components/layout/Layout';
import { ToastContainer } from '@/components/common/Toast';
import { LandingUpload } from '@/pages/LandingUpload';
import { Dashboard } from '@/pages/Dashboard';
import { Positions } from '@/pages/Positions';
import { PositionDetail } from '@/pages/PositionDetail';
import { Statistics } from '@/pages/Statistics';
import { System } from '@/pages/System';
import { AICoach } from '@/pages/AICoach';
import { TaskStatus } from '@/pages/TaskStatus';
import { EventAnalysis } from '@/pages/EventAnalysis';

function App() {
  return (
    <BrowserRouter>
      <ToastContainer />
      <Routes>
        {/* Landing Page - No Layout */}
        <Route path="/" element={<LandingUpload />} />

        {/* Main App with Layout */}
        <Route element={<Layout />}>
          <Route path="statistics" element={<Statistics />} />
          <Route path="positions" element={<Positions />} />
          <Route path="positions/:id" element={<PositionDetail />} />
          <Route path="events" element={<EventAnalysis />} />
          <Route path="tasks/:taskId" element={<TaskStatus />} />

          {/* Hidden routes (accessible via URL but not in nav) */}
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="ai-coach" element={<AICoach />} />
          <Route path="upload" element={<Navigate to="/" replace />} />
          <Route path="system" element={<System />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
