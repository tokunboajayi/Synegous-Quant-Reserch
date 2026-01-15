import { HashRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/Layout';
import { ControlCenter } from './pages/ControlCenter';
import { PipelineGraph } from './pages/PipelineGraph';
import { RunDetail } from './pages/RunDetail';
import { OrderStudio } from './pages/OrderStudio';
import { StrategyBuilder } from './pages/StrategyBuilder';
import { MarketResearch } from './pages/MarketResearch';
import { ResultsDashboard } from './pages/ResultsDashboard';
import { PortfolioIntelligence } from './pages/PortfolioIntelligence';
import { NexusOrchestrator } from './pages/NexusOrchestrator';

function App() {
  return (
    <HashRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<PipelineGraph />} />
          <Route path="/runs/:runId" element={<RunDetail />} />
          <Route path="/control" element={<ControlCenter />} />
          <Route path="/results" element={<ResultsDashboard />} />
          <Route path="/playback" element={<OrderStudio />} />
          <Route path="/research" element={<StrategyBuilder />} />
          <Route path="/market" element={<MarketResearch />} />
          <Route path="/intelligence" element={<PortfolioIntelligence />} />
          <Route path="/nexus" element={<NexusOrchestrator />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Layout>
    </HashRouter>
  );
}

export default App;
