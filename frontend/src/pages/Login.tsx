import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import {
  LogIn,
  Key,
  Mail,
  ShieldAlert,
  Loader2,
  Car,
  BrainCircuit,
  ShieldCheck,
} from "lucide-react";
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
      window.location.reload();
    } catch (err: any) {
      setError(err.message || "Invalid credentials.");
    } finally {
      setLoading(false);
    }
  };

  const loginAsPreset = async (
    presetEmail: string,
    presetPass: string
  ) => {
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
    <div className="relative min-h-[calc(100vh-80px)] flex items-center justify-center px-4 py-12 overflow-hidden">
      {/* Background glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[500px] h-[500px] bg-accent-cyan/5 rounded-full blur-[120px] pointer-events-none" />

      <div className="relative w-full max-w-md">
        {/* Brand */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-accent-blue/20 to-accent-cyan/20 border border-accent-cyan/20 mb-5 shadow-[0_0_30px_rgba(0,242,254,0.08)]">
            <Car className="text-accent-cyan" size={28} />
          </div>

          <h1 className="text-3xl font-bold tracking-tight text-white">
            Welcome to{" "}
            <span className="text-accent-cyan neon-text-glow">
              ParkIQ
            </span>
          </h1>

          <p className="text-sm text-slate-400 mt-2">
            Intelligent parking. Powered by AI.
          </p>
        </div>

        {/* Login card */}
        <div className="glass-panel p-7 sm:p-8 relative overflow-hidden">
          {/* Top accent */}
          <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-accent-cyan/60 to-transparent" />

          <div className="mb-6">
            <h2 className="text-lg font-semibold text-white">
              Sign in to your account
            </h2>
            <p className="text-xs text-slate-500 mt-1">
              Access your parking dashboard and intelligence tools.
            </p>
          </div>

          {/* Error */}
          {error && (
            <div className="flex items-start gap-3 bg-red-950/30 border border-red-500/20 text-red-400 px-4 py-3 rounded-lg text-sm mb-5">
              <ShieldAlert size={18} className="mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-5">
            {/* Email */}
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-2">
                Email address
              </label>

              <div className="relative group">
                <Mail
                  size={17}
                  className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-accent-cyan transition-colors"
                />

                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  autoComplete="email"
                  className="w-full pl-11 pr-4 py-3 bg-[#0b1220] border border-white/[0.08] rounded-lg text-sm text-white placeholder-slate-600 outline-none transition-all focus:border-accent-cyan/50 focus:ring-2 focus:ring-accent-cyan/10 hover:border-white/[0.14]"
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-2">
                Password
              </label>

              <div className="relative group">
                <Key
                  size={17}
                  className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-accent-cyan transition-colors"
                />

                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  autoComplete="current-password"
                  className="w-full pl-11 pr-4 py-3 bg-[#0b1220] border border-white/[0.08] rounded-lg text-sm text-white placeholder-slate-600 outline-none transition-all focus:border-accent-cyan/50 focus:ring-2 focus:ring-accent-cyan/10 hover:border-white/[0.14]"
                />
              </div>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-accent-blue to-accent-cyan text-slate-950 font-semibold py-3 rounded-lg hover:shadow-[0_0_24px_rgba(0,242,254,0.25)] hover:-translate-y-0.5 transition-all duration-200 disabled:opacity-60 disabled:hover:translate-y-0 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <Loader2 size={18} className="animate-spin" />
                  Signing in...
                </>
              ) : (
                <>
                  <LogIn size={18} />
                  Sign In
                </>
              )}
            </button>
          </form>

          {/* Demo accounts */}
          <div className="relative my-7">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-white/[0.07]" />
            </div>

            <div className="relative flex justify-center">
              <span className="bg-[#090d16] px-3 text-[10px] uppercase tracking-[0.15em] text-slate-600">
                Demo access
              </span>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-2">
            <button
              type="button"
              onClick={() =>
                loginAsPreset("driver@parkiq.com", "driver123")
              }
              disabled={loading}
              className="py-2.5 rounded-lg bg-white/[0.03] border border-white/[0.07] text-xs font-medium text-slate-400 hover:text-status-vacant hover:border-status-vacant/40 hover:bg-status-vacant/5 transition-all disabled:opacity-50"
            >
              Driver
            </button>

            <button
              type="button"
              onClick={() =>
                loginAsPreset("staff@parkiq.com", "staff123")
              }
              disabled={loading}
              className="py-2.5 rounded-lg bg-white/[0.03] border border-white/[0.07] text-xs font-medium text-slate-400 hover:text-accent-cyan hover:border-accent-cyan/40 hover:bg-accent-cyan/5 transition-all disabled:opacity-50"
            >
              Staff
            </button>

            <button
              type="button"
              onClick={() =>
                loginAsPreset("admin@parkiq.com", "admin123")
              }
              disabled={loading}
              className="py-2.5 rounded-lg bg-white/[0.03] border border-white/[0.07] text-xs font-medium text-slate-400 hover:text-status-reserved hover:border-status-reserved/40 hover:bg-status-reserved/5 transition-all disabled:opacity-50"
            >
              Manager
            </button>
          </div>

          {/* Security indicators */}
          <div className="grid grid-cols-3 gap-2 mt-6 pt-5 border-t border-white/[0.06]">
            <div className="flex flex-col items-center gap-1.5 text-center">
              <ShieldCheck size={15} className="text-status-vacant" />
              <span className="text-[9px] text-slate-600">
                Secure Access
              </span>
            </div>

            <div className="flex flex-col items-center gap-1.5 text-center">
              <BrainCircuit size={15} className="text-accent-cyan" />
              <span className="text-[9px] text-slate-600">
                AI Powered
              </span>
            </div>

            <div className="flex flex-col items-center gap-1.5 text-center">
              <Key size={15} className="text-accent-blue" />
              <span className="text-[9px] text-slate-600">
                JWT Protected
              </span>
            </div>
          </div>

          {/* Register */}
          <div className="mt-6 text-center text-sm text-slate-500">
            New to ParkIQ?{" "}
            <Link
              to="/register"
              className="text-accent-cyan hover:text-accent-neon transition-colors font-medium"
            >
              Create an account
            </Link>
          </div>
        </div>

        <p className="text-center text-[10px] text-slate-700 mt-5">
          ParkIQ Intelligence Platform • Secure parking management
        </p>
      </div>
    </div>
  );
}
