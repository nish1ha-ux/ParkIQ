import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { LogIn, Key, Mail, ShieldAlert } from "lucide-react";
import { api } from "../services/api";

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await api.auth.login(email, password);
      navigate("/");
      // Force page reload to trigger WebSocket connection & layout updates
      window.location.reload();
    } catch (err: any) {
      setError(err.message || "Invalid credentials.");
    } finally {
      setLoading(false);
    }
  };

  const loginAsPreset = async (presetEmail: string, presetPass: string) => {
    setError("");
    setLoading(true);
    try {
      await api.auth.login(presetEmail, presetPass);
      navigate("/");
      window.location.reload();
    } catch (err: any) {
      setError(err.message || "Failed preset login.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-[85vh] px-4">
      <div className="glass-panel w-full max-w-md p-8 relative overflow-hidden">
        {/* Glow accent */}
        <div className="absolute -top-10 -right-10 w-32 h-32 bg-accent-cyan/10 rounded-full blur-2xl"></div>

        <div className="text-center mb-8">
          <h2 className="text-3xl font-extrabold tracking-tight text-white font-sans">
            Welcome to <span className="text-accent-cyan neon-text-glow">ParkIQ</span>
          </h2>
          <p className="text-slate-400 text-sm mt-2">
            Smart AI-Powered Parking Intelligence Platform
          </p>
        </div>

        {error && (
          <div className="flex items-center gap-2 bg-red-950/40 border border-red-500/30 text-red-400 px-4 py-3 rounded-lg text-sm mb-6">
            <ShieldAlert size={18} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleLogin} className="space-y-5">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
              Email Address
            </label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-500">
                <Mail size={16} />
              </span>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="driver@parkiq.com"
                className="w-full pl-10 pr-4 py-3 bg-[#0d1426]/80 border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-accent-cyan transition-all text-sm"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
              Password
            </label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-500">
                <Key size={16} />
              </span>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full pl-10 pr-4 py-3 bg-[#0d1426]/80 border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-accent-cyan transition-all text-sm"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-accent-blue to-accent-cyan text-slate-900 font-bold py-3 px-4 rounded-lg hover:shadow-[0_0_15px_rgba(0,242,254,0.5)] transition-all disabled:opacity-50 text-sm"
          >
            <LogIn size={18} />
            {loading ? "Authenticating..." : "Sign In"}
          </button>
        </form>

        <div className="relative my-8">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-white/10"></div>
          </div>
          <div className="relative flex justify-center text-xs uppercase">
            <span className="bg-[#0b101f] px-2 text-slate-500">Demo Shortcuts</span>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-2">
          <button
            onClick={() => loginAsPreset("driver@parkiq.com", "driver123")}
            className="text-xs bg-white/5 border border-white/10 hover:border-status-vacant hover:bg-status-vacant/5 text-slate-300 hover:text-status-vacant py-2 px-1 rounded-md transition-all font-medium"
          >
            Driver
          </button>
          <button
            onClick={() => loginAsPreset("staff@parkiq.com", "staff123")}
            className="text-xs bg-white/5 border border-white/10 hover:border-accent-cyan hover:bg-accent-cyan/5 text-slate-300 hover:text-accent-cyan py-2 px-1 rounded-md transition-all font-medium"
          >
            Staff
          </button>
          <button
            onClick={() => loginAsPreset("admin@parkiq.com", "admin123")}
            className="text-xs bg-white/5 border border-white/10 hover:border-status-reserved hover:bg-status-reserved/5 text-slate-300 hover:text-status-reserved py-2 px-1 rounded-md transition-all font-medium"
          >
            Manager
          </button>
        </div>

        <div className="mt-8 text-center text-sm text-slate-400">
          New to ParkIQ?{" "}
          <Link to="/register" className="text-accent-cyan hover:underline">
            Create an account
          </Link>
        </div>
      </div>
    </div>
  );
}
