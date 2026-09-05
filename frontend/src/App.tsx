import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { LandingPage } from './pages/LandingPage';
import { AppLayout } from './components/layout/AppLayout';
import { OverviewDashboard } from './pages/OverviewDashboard';
import { InvestigationsPage } from './pages/InvestigationsPage';
import { InvestigationWorkspacePage } from './pages/InvestigationWorkspacePage';
import { LiveMaritimePage } from './pages/LiveMaritimePage';
import { VesselsPage } from './pages/VesselsPage';
import { DataSourcesPage } from './pages/DataSourcesPage';
import { ReportsPage } from './pages/ReportsPage';
import { SettingsPage } from './pages/SettingsPage';
import { AuthProvider } from './context/AuthContext';

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
        {/* 1. Public Landing Page */}
        <Route path="/" element={<LandingPage />} />

        {/* 2. Enterprise Application Workspace with Persistent AppLayout */}
        <Route path="/app" element={<AppLayout />}>
          <Route index element={<OverviewDashboard />} />
          <Route path="dashboard" element={<Navigate to="/app" replace />} />
          <Route path="investigations" element={<InvestigationsPage />} />
          <Route path="investigations/:caseId" element={<InvestigationWorkspacePage />} />
          <Route path="live" element={<LiveMaritimePage />} />
          <Route path="vessels" element={<VesselsPage />} />
          <Route path="data-sources" element={<DataSourcesPage />} />
          <Route path="reports" element={<ReportsPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>

        {/* Catch-all redirects to landing page */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
    </AuthProvider>
  );
};

export default App;
