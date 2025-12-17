import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from '@/components/layout/Layout';
import { Dashboard } from '@/pages/Dashboard';
import { Positions } from '@/pages/Positions';
import { PositionDetail } from '@/pages/PositionDetail';
import { Statistics } from '@/pages/Statistics';
import { System } from '@/pages/System';
import { AICoach } from '@/pages/AICoach';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="positions" element={<Positions />} />
          <Route path="positions/:id" element={<PositionDetail />} />
          <Route path="statistics" element={<Statistics />} />
          <Route path="ai-coach" element={<AICoach />} />
          <Route path="system" element={<System />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
