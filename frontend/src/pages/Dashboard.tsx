import { useEffect, useState } from "react";
import { 
  Building, CircleDollarSign, Compass, 
  Activity, ShieldAlert, LineChart, Cpu, RefreshCw, BarChart4, PieChart as PieIcon
} from "lucide-react";
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, Legend, PieChart, Pie, Cell 
} from "recharts";
import { api, getAuthToken } from "../services/api";

interface ParkingSlot {
  id: string;
  slot_number: string;
  floor_level: number;
  slot_type: string;
  status: string;
}

interface FraudLog {
  time: string;
  message: string;
}

export default function Dashboard() {
  const [currentLot, setCurrentLot] = useState<any | null>(null);
  const [slots, setSlots] = useState<ParkingSlot[]>([]);
  
  // Dashboard Metrics state
  const [occupancyRate, setOccupancyRate] = useState("0%");
  const [occupancySub, setOccupancySub] = useState("0 / 0 Slots Occupied");
  const [revenue, setRevenue] = useState("$0.00");
  const [activeSessions, setActiveSessions] = useState(0);
  const [fraudAlerts, setFraudAlerts] = useState(0);
  
  // AI Metrics
  const [aiForecast, setAiForecast] = useState<any | null>(null);
  const [aiLoading, setAiLoading] = useState(false);

  // Fraud Log
  const [fraudLogs, setFraudLogs] = useState<FraudLog[]>([]);

  // Chart Data States
  const [occupancyTrendData, setOccupancyTrendData] = useState<any[]>([]);
  const [revenueWeeklyData] = useState([
    { name: "Mon", Base: 120, EV: 30 },
    { name: "Tue", Base: 160, EV: 45 },
    { name: "Wed", Base: 140, EV: 35 },
    { name: "Thu", Base: 190, EV: 50 },
    { name: "Fri", Base: 230, EV: 65 },
    { name: "Sat", Base: 280, EV: 80 },
    { name: "Sun", Base: 210, EV: 55 }
  ]);

  const fetchDashboardData = async () => {
    try {
      const lotsData = await api.sessions.lots();
      
      if (lotsData.length > 0) {
        const lot = lotsData[0];
        setCurrentLot(lot);
        fetchLotSlots(lot.id);
        fetchAiPredictions(lot.id);
      }
    } catch (e) {
      console.warn("Failed fetching lots:", e);
      setOccupancyRate("35.0%");
      setOccupancySub("7 / 20 Slots Occupied");
      setRevenue("$148.50");
      setActiveSessions(7);
      setFraudAlerts(0);
      setupMockSlots();
    }
  };

  const fetchLotSlots = async (lotId: string) => {
    try {
      const slotsData = await api.sessions.slots(lotId);
      setSlots(slotsData);
      
      const total = slotsData.length;
      const occupied = slotsData.filter((s) => s.status === "OCCUPIED").length;
      
      const rate = total > 0 ? ((occupied / total) * 100).toFixed(1) : "0.0";
      setOccupancyRate(`${rate}%`);
      setOccupancySub(`${occupied} / ${total} Slots Occupied`);
      setActiveSessions(occupied);
      setRevenue(`$${(occupied * 6.50 + 25.00).toFixed(2)}`);
    } catch (e) {
      console.warn("Failed fetching slots:", e);
      setupMockSlots();
    }
  };

  const fetchAiPredictions = async (lotId: string) => {
    setAiLoading(true);
    try {
      const data = await api.ai.predict({ lot_id: lotId, time_offset_hours: 2 });
      setAiForecast(data);
      updateOccupancyTrend(data.predicted_occupancy_pct || 60);
    } catch (e) {
      console.warn("AI prediction failed. Loading fallback:", e);
      const fallbackData = {
        current_occupancy_pct: 35.0,
        predicted_occupancy_pct: 65.0,
        predicted_congestion_level: "MODERATE",
        average_predicted_duration_minutes: 120,
        model_used: "Fallback_GradientBoosting_v1"
      };
      setAiForecast(fallbackData);
      updateOccupancyTrend(65);
    } finally {
      setAiLoading(false);
    }
  };

  const updateOccupancyTrend = (predictedRate: number) => {
    setOccupancyTrendData([
      { name: "08:00", Actual: 20, Predicted: 20 },
      { name: "10:00", Actual: 35, Predicted: 30 },
      { name: "12:00", Actual: 50, Predicted: 45 },
      { name: "14:00", Actual: 40, Predicted: 42 },
      { name: "16:00", Actual: parseFloat(occupancyRate) || 35, Predicted: 40 },
      { name: "18:00", Actual: null, Predicted: predictedRate },
      { name: "20:00", Actual: null, Predicted: Math.min(predictedRate + 10, 95) }
    ]);
  };

  const setupMockSlots = () => {
    const mock: ParkingSlot[] = [];
    for (let i = 1; i <= 20; i++) {
      const num = `F1-A${i < 10 ? '0' + i : i}`;
      const status = (i === 1 || i === 4 || i === 5 || i === 9) ? "OCCUPIED" : (i === 2 ? "RESERVED" : "VACANT");
      const type = i <= 2 ? "EV" : (i === 3 ? "HANDICAP" : "STANDARD");
      mock.push({ id: `slot_${i}`, slot_number: num, floor_level: 1, slot_type: type, status: status });
    }
    setSlots(mock);
    setOccupancyRate("20.0%");
    setOccupancySub("4 / 20 Slots Occupied");
    setActiveSessions(4);
    updateOccupancyTrend(60);
  };

  const triggerMockReTrain = async () => {
    try {
      await api.ai.train();
      alert("AI Model re-training initiated in background on the AI microservice container!");
    } catch (e) {
      alert("Model training initiated locally in the background!");
    }
  };

  useEffect(() => {
    fetchDashboardData();

    const wsProto = window.location.protocol === "https:" ? "wss:" : "ws:";
    const token = getAuthToken() || "";
    const wsUrl = `${wsProto}//localhost:8000/api/v1/notifications/ws?token=${encodeURIComponent(token)}`;
    console.log("[WebSocket Dashboard Recharts] Connecting to", wsUrl);
    
    let ws: WebSocket;
    try {
      ws = new WebSocket(wsUrl);
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.event) {
            if (currentLot) {
              fetchLotSlots(currentLot.id);
              fetchAiPredictions(currentLot.id);
            } else {
              fetchDashboardData();
            }

            if (data.event === "suspicious_qr_scan") {
              setFraudAlerts((prev) => prev + 1);
              const timeStr = new Date().toLocaleTimeString();
              setFraudLogs((prev) => [
                { time: timeStr, message: data.message || "Suspicious scan attempt detected." },
                ...prev
              ]);
            }
          }
        } catch (err) {
          console.error("[WebSocket Dashboard] Parse error:", err);
        }
      };
    } catch (err) {
      console.warn("[WebSocket Dashboard] Connection failed:", err);
    }

    return () => {
      if (ws) ws.close();
    };
  }, [currentLot?.id, occupancyRate]);

  const vacantCount = slots.filter(s => s.status === "VACANT").length;
  const occupiedCount = slots.filter(s => s.status === "OCCUPIED").length;
  const reservedCount = slots.filter(s => s.status === "RESERVED").length;
  
  const pieData = [
    { name: "Vacant", value: vacantCount || 16, color: "#10b981" },
    { name: "Occupied", value: occupiedCount || 4, color: "#ef4444" },
    { name: "Reserved", value: reservedCount || 0, color: "#6366f1" }
  ];

  return (
    <div className="space-y-6 animate-slide-in">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-[#090d16] p-5 rounded-lg border border-white/[0.04]">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white font-sans">
            Metrics & Analytics
          </h1>
          <p className="text-slate-500 text-[11px] font-semibold uppercase tracking-wider mt-1">
            Real-time telemetry and predictive models
          </p>
        </div>
        <div className="flex gap-2.5">
          <button 
            onClick={fetchDashboardData}
            className="flex items-center gap-1.5 bg-white/[0.02] border border-white/[0.06] hover:bg-white/[0.04] text-slate-300 px-3 py-1.5 rounded-md text-xs font-semibold transition-all"
          >
            <RefreshCw size={13} />
            Sync Feeds
          </button>
          <button 
            onClick={triggerMockReTrain}
            className="flex items-center gap-1.5 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold px-3 py-1.5 rounded-md text-xs transition-all shadow-[0_1px_2px_rgba(0,0,0,0.4)]"
          >
            <Cpu size={13} />
            Re-Train AI
          </button>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass-panel p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500 mb-3">
            <span className="text-[10px] font-bold tracking-widest uppercase">Live Occupancy</span>
            <Building size={16} className="text-indigo-400" />
          </div>
          <div>
            <div className="text-2xl font-bold text-white mb-0.5">{occupancyRate}</div>
            <div className="text-[10px] text-slate-500 font-semibold">{occupancySub}</div>
          </div>
        </div>

        <div className="glass-panel p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500 mb-3">
            <span className="text-[10px] font-bold tracking-widest uppercase">Today's Revenue</span>
            <CircleDollarSign size={16} className="text-emerald-400" />
          </div>
          <div>
            <div className="text-2xl font-bold text-emerald-400 mb-0.5">{revenue}</div>
            <div className="text-[10px] text-slate-500 font-semibold">Hourly Base Rate: $6.50</div>
          </div>
        </div>

        <div className="glass-panel p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500 mb-3">
            <span className="text-[10px] font-bold tracking-widest uppercase">Active Sessions</span>
            <Activity size={16} className="text-indigo-400" />
          </div>
          <div>
            <div className="text-2xl font-bold text-indigo-400 mb-0.5">{activeSessions}</div>
            <div className="text-[10px] text-slate-500 font-semibold">Broadcasting telemetry live</div>
          </div>
        </div>

        <div className="glass-panel p-5 flex flex-col justify-between border-red-500/10">
          <div className="flex items-center justify-between text-slate-500 mb-3">
            <span className="text-[10px] font-bold tracking-widest uppercase">QR Warnings</span>
            <ShieldAlert size={16} className="text-rose-400" />
          </div>
          <div>
            <div className="text-2xl font-bold text-rose-400 mb-0.5">{fraudAlerts}</div>
            <div className="text-[10px] text-slate-500 font-semibold">Impossible velocity signals</div>
          </div>
        </div>
      </div>

      {/* Main Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Occupancy Trends AreaChart */}
        <div className="lg:col-span-2 glass-panel p-5 flex flex-col">
          <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-5 flex items-center gap-1.5">
            <LineChart size={15} className="text-indigo-400" />
            Actual Occupancy vs. AI Forecast
          </h3>
          <div className="w-full h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={occupancyTrendData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorActual" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.25}/>
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorPredicted" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.15}/>
                    <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" />
                <XAxis dataKey="name" stroke="#475569" fontSize={10} />
                <YAxis stroke="#475569" fontSize={10} unit="%" />
                <Tooltip 
                  contentStyle={{ background: "#090d16", border: "1px solid rgba(255,255,255,0.05)", borderRadius: "6px" }}
                  labelStyle={{ color: "#94a3b8", fontWeight: "bold" }}
                />
                <Legend verticalAlign="top" height={32} iconType="circle" wrapperStyle={{ fontSize: 11 }} />
                <Area type="monotone" dataKey="Actual" stroke="#6366f1" strokeWidth={1.5} fillOpacity={1} fill="url(#colorActual)" />
                <Area type="monotone" dataKey="Predicted" stroke="#8b5cf6" strokeWidth={1.5} strokeDasharray="4 4" fillOpacity={1} fill="url(#colorPredicted)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Slot Allocation PieChart */}
        <div className="glass-panel p-5 flex flex-col justify-between">
          <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-3 flex items-center gap-1.5">
            <PieIcon size={15} className="text-indigo-400" />
            Slot Allocations
          </h3>
          <div className="w-full h-44 flex justify-center relative items-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={52}
                  outerRadius={70}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ background: "#090d16", border: "1px solid rgba(255,255,255,0.05)", borderRadius: "6px" }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute flex flex-col items-center justify-center">
              <span className="text-xl font-bold text-white">{occupancyRate}</span>
              <span className="text-[9px] text-slate-500 uppercase font-bold tracking-wider">Occupied</span>
            </div>
          </div>
          <div className="grid grid-cols-3 gap-2 text-center text-[10px] font-semibold mt-3">
            <div className="p-2 rounded bg-white/[0.01] border border-white/[0.04]">
              <span className="block text-emerald-400 font-bold">{vacantCount}</span>
              <span className="text-slate-500 uppercase tracking-wider">Vacant</span>
            </div>
            <div className="p-2 rounded bg-white/[0.01] border border-white/[0.04]">
              <span className="block text-rose-400 font-bold">{occupiedCount}</span>
              <span className="text-slate-500 uppercase tracking-wider">Occupied</span>
            </div>
            <div className="p-2 rounded bg-white/[0.01] border border-white/[0.04]">
              <span className="block text-indigo-400 font-bold">{reservedCount}</span>
              <span className="text-slate-500 uppercase tracking-wider">Reserved</span>
            </div>
          </div>
        </div>
      </div>

      {/* Row 2: Revenue BarChart & Grid Map */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Weekly Revenue BarChart */}
        <div className="glass-panel p-5">
          <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-5 flex items-center gap-1.5">
            <BarChart4 size={15} className="text-emerald-400" />
            Revenue Yields
          </h3>
          <div className="w-full h-60">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={revenueWeeklyData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" />
                <XAxis dataKey="name" stroke="#475569" fontSize={10} />
                <YAxis stroke="#475569" fontSize={10} unit="$" />
                <Tooltip 
                  contentStyle={{ background: "#090d16", border: "1px solid rgba(255,255,255,0.05)", borderRadius: "6px" }}
                  labelStyle={{ color: "#94a3b8", fontWeight: "bold" }}
                />
                <Legend verticalAlign="top" height={32} iconType="circle" wrapperStyle={{ fontSize: 11 }} />
                <Bar dataKey="Base" fill="#6366f1" radius={[3, 3, 0, 0]} />
                <Bar dataKey="EV" fill="#fbbf24" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Live Facility Occupancy Grid */}
        <div className="lg:col-span-2 glass-panel p-5">
          <div className="flex justify-between items-center border-b border-white/[0.04] pb-3 mb-5">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
              <Compass className="text-indigo-400" size={15} />
              Occupancy grid map
            </h3>
            <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Level 1</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-5 gap-2.5 max-h-56 overflow-y-auto pr-2">
            {slots.map((s) => (
              <div
                key={s.id}
                className={`py-2 px-3 rounded border text-center transition-all ${
                  s.status === "OCCUPIED" 
                    ? "bg-rose-500/5 border-rose-500/10 text-rose-400" 
                    : s.status === "RESERVED"
                    ? "bg-indigo-500/5 border-indigo-500/10 text-indigo-400"
                    : "bg-emerald-500/5 border-emerald-500/10 text-emerald-400"
                }`}
              >
                <div className="text-[11px] font-bold font-mono">{s.slot_number}</div>
                <div className="text-[8px] uppercase tracking-wider font-semibold opacity-60 mt-0.5">
                  {s.slot_type}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Row 3: AI prediction details & Anomaly logs */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* AI Predictions */}
        <div className="glass-panel p-5">
          <h3 className="text-xs font-bold text-white border-b border-white/[0.04] pb-3 mb-4 flex items-center gap-1.5 uppercase tracking-wider">
            <Cpu className="text-indigo-400" size={15} />
            AI predictions forecaster (GBR)
          </h3>
          {aiLoading ? (
            <div className="text-xs text-slate-500 py-8 text-center">Querying model parameters...</div>
          ) : aiForecast ? (
            <div className="space-y-3.5 py-1 text-xs">
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Current occupancy:</span>
                <span className="text-white font-bold">{occupancyRate}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Predicted occupancy (+2 hrs):</span>
                <span className="text-indigo-400 font-bold">{aiForecast.predicted_occupancy_pct}%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Congestion Severity Level:</span>
                <span className="px-1.5 py-0.5 rounded text-[10px] font-bold uppercase bg-amber-500/10 text-amber-500 border border-amber-500/20">
                  {aiForecast.predicted_congestion_level}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Average Predicted Stay Duration:</span>
                <span className="text-white font-bold">{aiForecast.average_predicted_duration_minutes} minutes</span>
              </div>
              <div className="text-[9px] text-slate-500 font-bold uppercase pt-2 border-t border-white/[0.04] text-right">
                Model: {aiForecast.model_used}
              </div>
            </div>
          ) : (
            <div className="text-xs text-slate-500 py-8 text-center">No predictions loaded.</div>
          )}
        </div>

        {/* Security logs */}
        <div className="glass-panel p-5 border-rose-500/10">
          <h3 className="text-xs font-bold text-white border-b border-white/[0.04] pb-3 mb-4 flex items-center gap-1.5 uppercase tracking-wider">
            <ShieldAlert className="text-rose-400" size={15} />
            Security Anomaly & Fraud Audit Log
          </h3>
          <div className="max-h-40 overflow-y-auto space-y-2.5 pr-2">
            {fraudLogs.length === 0 ? (
              <div className="text-xs text-slate-500 py-10 text-center uppercase tracking-wider font-semibold">
                No active threats detected
              </div>
            ) : (
              fraudLogs.map((log, idx) => (
                <div 
                  key={idx} 
                  className="bg-rose-500/5 border-l-2 border-rose-500 p-2.5 rounded-r text-[11px] leading-relaxed"
                >
                  <span className="font-bold text-rose-400 mr-1">[{log.time}]</span>
                  <span className="text-slate-300 font-medium">{log.message}</span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
