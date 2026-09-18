import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { UserPlus, User as UserIcon, Mail, Phone, Key, ShieldAlert } from "lucide-react";
import { api } from "../services/api";

export default function Register() {
  const navigate = useNavigate();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await api.auth.register({
        full_name: fullName,
        email,
        phone,
        password,
      });
      setSuccess(true);
      setTimeout(() => {
        navigate("/login");
      }, 2000);
    } catch (err: any) {
      setError(err.message || "Registration failed. Try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-[85vh] px-4">
      <div className="glass-panel w-full max-w-md p-8 relative overflow-hidden">
        {/* Glow accent */}
        <div className="absolute -top-10 -left-10 w-32 h-32 bg-accent-blue/10 rounded-full blur-2xl"></div>

        <div className="text-center mb-8">
          <h2 className="text-3xl font-extrabold tracking-tight text-white font-sans">
            Join <span className="text-accent-blue">ParkIQ</span>
          </h2>
          <p className="text-slate-400 text-sm mt-2">
            Create an account to start ticketless smart parking
          </p>
        </div>

        {error && (
          <div className="flex items-center gap-2 bg-red-950/40 border border-red-500/30 text-red-400 px-4 py-3 rounded-lg text-sm mb-6">
            <ShieldAlert size={18} />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div className="bg-emerald-950/40 border border-emerald-500/30 text-emerald-400 px-4 py-3 rounded-lg text-sm mb-6 text-center">
            Registration successful! Redirecting to login...
          </div>
        )}

        <form onSubmit={handleRegister} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
              Full Name
            </label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-500">
                <UserIcon size={16} />
              </span>
              <input
                type="text"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="John Doe"
                className="w-full pl-10 pr-4 py-3 bg-[#0d1426]/80 border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-accent-blue transition-all text-sm"
              />
            </div>
          </div>

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
                placeholder="john@example.com"
                className="w-full pl-10 pr-4 py-3 bg-[#0d1426]/80 border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-accent-blue transition-all text-sm"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
              Phone Number
            </label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-500">
                <Phone size={16} />
              </span>
              <input
                type="text"
                required
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="+1 555-0199"
                className="w-full pl-10 pr-4 py-3 bg-[#0d1426]/80 border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-accent-blue transition-all text-sm"
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
                className="w-full pl-10 pr-4 py-3 bg-[#0d1426]/80 border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-accent-blue transition-all text-sm"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading || success}
            className="w-full mt-2 flex items-center justify-center gap-2 bg-gradient-to-r from-accent-blue to-accent-cyan text-slate-900 font-bold py-3 px-4 rounded-lg hover:shadow-[0_0_15px_rgba(79,172,254,0.5)] transition-all disabled:opacity-50 text-sm"
          >
            <UserPlus size={18} />
            {loading ? "Registering..." : "Create Account"}
          </button>
        </form>

        <div className="mt-8 text-center text-sm text-slate-400">
          Already have an account?{" "}
          <Link to="/login" className="text-accent-blue hover:underline">
            Sign In
          </Link>
        </div>
      </div>
    </div>
  );
}
