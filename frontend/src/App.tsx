import { Routes, Route } from "react-router-dom";
import { AppLayout } from "./layouts/AppLayout";
import { BrandLayout } from "./layouts/BrandLayout";
import { RequireAuth } from "./components/RequireAuth";
import { Login } from "./pages/Login";
import { Signup } from "./pages/Signup";
import { PortfolioHome } from "./pages/PortfolioHome";
import { BrandOverview } from "./pages/BrandOverview";
import { DataHub } from "./pages/DataHub";
import { MarketLandscape } from "./pages/MarketLandscape";
import { EvidenceLibrary } from "./pages/EvidenceLibrary";
import { SegmentsTargeting } from "./pages/SegmentsTargeting";
import { PersonasJourneys } from "./pages/PersonasJourneys";
import { CompetitiveMap } from "./pages/CompetitiveMap";
import { BrandPlanPage } from "./pages/BrandPlanPage";
import { ChannelPlanner } from "./pages/ChannelPlanner";
import { Orchestration } from "./pages/Orchestration";
import { Measurement } from "./pages/Measurement";
import { Approvals } from "./pages/Approvals";
import { Admin } from "./pages/Admin";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />

      <Route element={<RequireAuth />}>
        <Route element={<AppLayout />}>
          <Route path="/" element={<PortfolioHome />} />
          <Route path="/admin" element={<Admin />} />
          <Route path="/brands/:brandId" element={<BrandLayout />}>
            <Route index element={<BrandOverview />} />
            <Route path="data-hub" element={<DataHub />} />
            <Route path="market-landscape" element={<MarketLandscape />} />
            <Route path="evidence" element={<EvidenceLibrary />} />
            <Route path="segments" element={<SegmentsTargeting />} />
            <Route path="personas" element={<PersonasJourneys />} />
            <Route path="competitive" element={<CompetitiveMap />} />
            <Route path="brand-plan" element={<BrandPlanPage />} />
            <Route path="channel-planner" element={<ChannelPlanner />} />
            <Route path="orchestration" element={<Orchestration />} />
            <Route path="measurement" element={<Measurement />} />
            <Route path="approvals" element={<Approvals />} />
          </Route>
        </Route>
      </Route>
    </Routes>
  );
}
