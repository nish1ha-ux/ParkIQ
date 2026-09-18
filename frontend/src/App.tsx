import React, { useEffect, useState } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate, Link, useLocation, useNavigate } from "react-router-dom";
import { 
  Building2, Car, Wallet, Clock, Bot, LogOut, 
  Menu, X, Bell, ShieldAlert, CirclePlay, Info
} from "lucide-react";
import { getAuthToken, api, getUserRole } from "./services/api";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import Vehicles from "./pages/Vehicles";
import WalletView from "./pages/Wallet";
import Sessions from "./pages/Sessions";
import Chat from "./pages/Chat";

interface Toast {
  id: number;
  event: string;
  message: string;
}

function MainLayout({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const userRole = getUserRole() || "DRIVER";

  useEffect(() => {
    const token = getAuthToken();
    if (!token) return;

    const wsProto = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${wsProto}//localhost:8000/api/v1/notifications/ws?token=${encodeURIComponent(token)}`;
    
    let ws: WebSocket;
    const connect = () => {
      console.log("[Global WebSocket] Connecting to feed...");
      ws = new WebSocket(wsUrl);
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.event) {
            const newToast: Toast = {
              id: Date.now(),
              event: data.event,
              message: data.message || "A new parking event has occurred."
            };
            setToasts((prev) => [...prev, newToast]);
            
            setTimeout(() => {
              setToasts((prev) => prev.filter((t) => t.id !== newToast.id));
            }, 5000);
          }
        } catch (e) {
          console.warn("Global WS message parse failed:", e);
        }
      };

      ws.onclose = () => {
        console.warn("Global WebSocket closed. Reconnecting in 5 seconds...");
        setTimeout(connect, 5000);
      };
    };

    connect();
    return () => {
      if (ws) ws.close();
    };
  }, []);

  const handleLogout = () => {
    api.auth.logout();
    navigate("/login");
  };

  const navItems = [
    { path: "/", label: "Dashboard", icon: Building2, roles: ["DRIVER", "STAFF", "ADMIN"] },
    { path: "/vehicles", label: "My Vehicles", icon: Car, roles: ["DRIVER", "ADMIN"] },
    { path: "/wallet", label: "QR Wallet", icon: Wallet, roles: ["DRIVER", "ADMIN"] },
    { path: "/sessions", label: "Sessions", icon: Clock, roles: ["DRIVER", "ADMIN"] },
    { path: "/chat", label: "AI Assistant", icon: Bot, roles: ["DRIVER", "STAFF", "ADMIN"] },
  ];

  const allowedNavItems = navItems.filter(item => item.roles.includes(userRole));

  return (
    <div className="flex min-h-screen bg-[#030712] text-slate-200 font-sans">
      {/* Sidebar - Desktop (Linear style) */}
      <aside className="hidden md:flex flex-col w-60 bg-[#070a13] border-r border-white/[0.04] p-5 flex-shrink-0">
        <div className="mb-8">
          <Link to="/" className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <span className="text-white font-sans font-black tracking-wide">Park<span className="text-indigo-400">IQ</span></span>
          </Link>
          <span className="text-[9px] uppercase font-bold tracking-widest text-slate-500 border border-white/[0.06] px-1.5 py-0.5 rounded-md mt-2.5 inline-block">
            {userRole} console
          </span>
        </div>

        <nav className="flex-1 space-y-1">
          {allowedNavItems.map((item) => {
            const Icon = item.icon;
            const active = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-2.5 px-3 py-2 rounded-md text-xs font-semibold transition-all ${
                  active 
                    ? "bg-indigo-500/10 text-indigo-400 border-l-2 border-indigo-400 font-bold" 
                    : "text-slate-400 hover:text-slate-200 hover:bg-white/[0.02]"
                }`}
              >
                <Icon size={16} />
                {item.label}
              </Link>
            );
          })}
        </nav>

        <button
          onClick={handleLogout}
          className="flex items-center gap-2.5 px-3 py-2 text-slate-400 hover:text-red-400 hover:bg-red-500/5 rounded-md text-xs font-semibold transition-all mt-auto"
        >
          <LogOut size={16} />
          Sign Out
        </button>
      </aside>

      {/* Main Container */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Navbar */}
        <header className="flex justify-between items-center bg-[#070a13] md:bg-transparent border-b border-white/[0.04] md:border-none p-4 md:px-8 md:py-5">
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden text-slate-400 hover:text-slate-200"
          >
            {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
          
          <Link to="/" className="md:hidden text-lg font-black text-white flex items-center gap-1">
            <span>Park<span className="text-indigo-400">IQ</span></span>
          </Link>

          <div className="flex items-center gap-4 ml-auto">
            <div className="text-slate-500 text-[10px] font-semibold hidden sm:flex items-center gap-1.5 uppercase tracking-wider">
              <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full"></span> Status: Online
            </div>
            <button className="relative text-slate-400 hover:text-slate-200 p-1.5 rounded-lg border border-white/[0.04] hover:bg-white/[0.02] transition-all">
              <Bell size={15} />
            </button>
          </div>
        </header>

        {/* Mobile Navigation Drawer */}
        {mobileMenuOpen && (
          <nav className="md:hidden bg-[#070a13] border-b border-white/[0.04] px-6 py-4 space-y-1.5 flex flex-col">
            {allowedNavItems.map((item) => {
              const Icon = item.icon;
              const active = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`flex items-center gap-2.5 px-3 py-2.5 rounded-md text-xs font-semibold ${
                    active 
                      ? "bg-indigo-500/10 text-indigo-400 border-l-2 border-indigo-400" 
                      : "text-slate-400 hover:text-slate-200 hover:bg-white/[0.02]"
                  }`}
                >
                  <Icon size={16} />
                  {item.label}
                </Link>
              );
            })}
            <button
              onClick={() => {
                setMobileMenuOpen(false);
                handleLogout();
              }}
              className="flex items-center gap-2.5 px-3 py-2.5 text-slate-400 hover:text-red-400 hover:bg-red-500/5 rounded-md text-xs font-semibold transition-all w-full text-left"
            >
              <LogOut size={16} />
              Sign Out
            </button>
          </nav>
        )}

        {/* Main Content Area */}
        <main className="flex-grow p-4 md:p-8 max-w-7xl w-full mx-auto overflow-y-auto">
          {children}
        </main>
      </div>

      {/* Floating Global Toasts (Vercel style) */}
      <div className="fixed bottom-6 right-6 z-[9999] flex flex-col gap-3">
        {toasts.map((toast) => {
          let icon = Info;
          let color = "text-indigo-400";
          let border = "border-white/[0.06]";
          let bg = "bg-[#090d16]/98";

          if (toast.event === "parking_started") {
            icon = CirclePlay;
            color = "text-emerald-400";
          } else if (toast.event === "parking_ending") {
            icon = ShieldAlert;
            color = "text-amber-500";
          } else if (toast.event === "parking_expired") {
            icon = ShieldAlert;
            color = "text-rose-500";
          } else if (toast.event === "suspicious_qr_scan") {
            icon = ShieldAlert;
            color = "text-rose-500";
            border = "border-rose-500/20";
            bg = "bg-rose-950/20";
          }
          const ToastIcon = icon;

          return (
            <div
              key={toast.id}
              className={`p-3.5 rounded-lg border ${border} ${bg} shadow-2xl flex items-start gap-3 w-76 animate-slide-in relative overflow-hidden`}
              style={{ boxShadow: '0 8px 30px rgba(0, 0, 0, 0.6)' }}
            >
              <div className={`${color} mt-0.5`}><ToastIcon size={18} /></div>
              <div className="flex-1 space-y-0.5">
                <div className="text-[10px] font-extrabold uppercase tracking-wider text-slate-300">
                  {toast.event.replace("_", " ")}
                </div>
                <div className="text-xs text-slate-400 leading-normal font-medium">
                  {toast.message}
                </div>
              </div>
              <button 
                onClick={() => setToasts((prev) => prev.filter((t) => t.id !== toast.id))}
                className="text-slate-500 hover:text-slate-300 p-0.5"
              >
                <X size={12} />
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const token = getAuthToken();
  return token ? <MainLayout>{children}</MainLayout> : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        
        {/* Protected Console Access Paths */}
        <Route path="/" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
        <Route path="/vehicles" element={<PrivateRoute><Vehicles /></PrivateRoute>} />
        <Route path="/wallet" element={<PrivateRoute><WalletView /></PrivateRoute>} />
        <Route path="/sessions" element={<PrivateRoute><Sessions /></PrivateRoute>} />
        <Route path="/chat" element={<PrivateRoute><Chat /></PrivateRoute>} />
        
        {/* Redirect all rest to home */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}
