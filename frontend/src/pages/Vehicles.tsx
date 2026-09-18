import React, { useEffect, useState } from "react";
import { Car, Plus, ShieldAlert } from "lucide-react";
import { api } from "../services/api";

interface Vehicle {
  id: string;
  license_plate: string;
  vehicle_type: string;
  created_at: string;
}

export default function Vehicles() {
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [loading, setLoading] = useState(true);
  const [plate, setPlate] = useState("");
  const [type, setType] = useState("SEDAN");
  const [error, setError] = useState("");
  const [adding, setAdding] = useState(false);

  const fetchVehicles = async () => {
    try {
      const data = await api.vehicles.list();
      setVehicles(data);
    } catch (e) {
      console.warn("Error fetching vehicles:", e);
    } finally {
      setLoading(false);
    }
  };

  const handleAddVehicle = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setAdding(true);

    try {
      await api.vehicles.create({ license_plate: plate.toUpperCase().trim(), vehicle_type: type });
      setPlate("");
      setType("SEDAN");
      fetchVehicles();
    } catch (err: any) {
      setError(err.message || "Failed to add vehicle.");
    } finally {
      setAdding(false);
    }
  };

  useEffect(() => {
    fetchVehicles();
  }, []);

  return (
    <div className="space-y-8 animate-slide-in">
      <div className="bg-slate-900/40 p-6 rounded-xl border border-white/5">
        <h1 className="text-3xl font-extrabold tracking-tight text-white">
          Vehicle <span className="text-accent-cyan neon-text-glow">Management</span>
        </h1>
        <p className="text-slate-400 text-sm mt-1">
          Register and configure your vehicles for automated ticketless parking entries
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Vehicles list */}
        <div className="lg:col-span-2 space-y-4">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Car className="text-accent-cyan" size={18} />
            My Registered Vehicles
          </h2>

          {loading ? (
            <div className="text-slate-400 text-sm py-8 text-center glass-panel">Loading...</div>
          ) : vehicles.length === 0 ? (
            <div className="text-slate-400 text-sm py-16 text-center glass-panel">
              No vehicles registered yet. Add one below to generate your QR Identity!
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {vehicles.map((v) => (
                <div key={v.id} className="glass-panel p-5 relative overflow-hidden">
                  <div className="absolute top-4 right-4 text-xs font-bold uppercase px-2 py-0.5 rounded bg-white/5 text-slate-300 border border-white/10">
                    {v.vehicle_type}
                  </div>
                  <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
                    LICENSE PLATE
                  </div>
                  <div className="text-2xl font-black text-white tracking-widest font-mono">
                    {v.license_plate}
                  </div>
                  <div className="text-[10px] text-slate-500 mt-4 font-semibold uppercase">
                    ID: {v.id.substring(0, 8)}...
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Add vehicle form */}
        <div className="glass-panel p-6 h-fit">
          <h3 className="text-lg font-bold text-white border-b border-white/5 pb-4 mb-5 flex items-center gap-2">
            <Plus className="text-accent-cyan" size={20} />
            Add Vehicle
          </h3>

          {error && (
            <div className="flex items-center gap-2 bg-red-950/40 border border-red-500/30 text-red-400 p-3 rounded-lg text-xs mb-4">
              <ShieldAlert size={16} />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleAddVehicle} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                License Plate
              </label>
              <input
                type="text"
                required
                value={plate}
                onChange={(e) => setPlate(e.target.value)}
                placeholder="MH-12-AB-1234"
                className="w-full px-4 py-3 bg-[#0d1426]/80 border border-white/10 rounded-lg text-white placeholder-slate-600 focus:outline-none focus:border-accent-cyan transition-all text-sm font-mono tracking-wider"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                Vehicle Type
              </label>
              <select
                value={type}
                onChange={(e) => setType(e.target.value)}
                className="w-full px-4 py-3 bg-[#0d1426]/80 border border-white/10 rounded-lg text-white focus:outline-none focus:border-accent-cyan transition-all text-sm font-semibold"
              >
                <option value="SEDAN">SEDAN</option>
                <option value="SUV">SUV</option>
                <option value="EV">EV CHARGER COMPATIBLE</option>
                <option value="BIKE">BIKE / MOTO</option>
              </select>
            </div>

            <button
              type="submit"
              disabled={adding}
              className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-accent-blue to-accent-cyan text-slate-900 font-bold py-3 px-4 rounded-lg hover:shadow-[0_0_15px_rgba(0,242,254,0.5)] transition-all disabled:opacity-50 text-sm mt-6"
            >
              Register Vehicle
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
