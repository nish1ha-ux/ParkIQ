import React, { useEffect, useState } from "react";
import { Play, Square, Timer, RefreshCcw, ShieldAlert, CreditCard, Sparkles } from "lucide-react";
import { api } from "../services/api";

interface Vehicle {
  id: string;
  license_plate: string;
  vehicle_type: string;
  qr_token: string;
}

interface ParkingSlot {
  id: string;
  slot_number: string;
  floor_level: number;
  slot_type: string;
  status: string;
}

export default function Sessions() {
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [selectedVehicle, setSelectedVehicle] = useState<Vehicle | null>(null);
  
  const [lots, setLots] = useState<any[]>([]);
  const [selectedLotId, setSelectedLotId] = useState("");
  const [slots, setSlots] = useState<ParkingSlot[]>([]);
  const [selectedSlotId, setSelectedSlotId] = useState("");
  
  const [expectedMinutes, setExpectedMinutes] = useState(60);
  const [activeSession, setActiveSession] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  
  // Extension state
  const [extendingMinutes, setExtendingMinutes] = useState(30);

  // Payment Checkout Simulation Modal
  const [showCheckout, setShowCheckout] = useState(false);
  const [checkoutData, setCheckoutData] = useState<any | null>(null);
  const [checkoutLoading, setCheckoutLoading] = useState(false);

  // AI Recommended Slot
  const [recommendedSlot, setRecommendedSlot] = useState<any | null>(null);

  const fetchInitialData = async () => {
    try {
      const vData = await api.vehicles.list();
      setVehicles(vData);
      if (vData.length > 0) {
        setSelectedVehicle(vData[0]);
      }

      const lData = await api.sessions.lots();
      setLots(lData);
      if (lData.length > 0) {
        setSelectedLotId(lData[0].id);
        fetchSlots(lData[0].id);
        fetchAiRecommendation(lData[0].id);
      }

      await checkActiveSession();
    } catch (e) {
      console.warn("Error fetching checkin details:", e);
    } finally {
      setLoading(false);
    }
  };

  const fetchSlots = async (lotId: string) => {
    try {
      const sData = await api.sessions.slots(lotId);
      setSlots(sData);
      const vacant = sData.filter((s) => s.status === "VACANT");
      if (vacant.length > 0) {
        setSelectedSlotId(vacant[0].id);
      }
    } catch (e) {
      console.warn("Error slots:", e);
    }
  };

  const fetchAiRecommendation = async (lotId: string) => {
    try {
      const rec = await api.ai.recommendSlot({ lot_id: lotId });
      setRecommendedSlot(rec);
    } catch (e) {
      console.warn("AI recommendation failed:", e);
    }
  };

  const checkActiveSession = async () => {
    try {
      const active = await api.sessions.active();
      if (active && active.length > 0) {
        // Just take the first active one for demo
        setActiveSession(active[0]);
      } else {
        setActiveSession(null);
      }
    } catch (e) {
      console.warn("Error checking active session:", e);
    }
  };

  const handleStartSession = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!selectedVehicle) {
      setError("Please register a vehicle first.");
      return;
    }
    if (!selectedSlotId) {
      setError("Please select a vacant parking slot.");
      return;
    }

    try {
      await api.sessions.start({
        qr_token: selectedVehicle.qr_token,
        slot_id: selectedSlotId,
        expected_duration_minutes: expectedMinutes
      });
      await checkActiveSession();
      if (selectedLotId) fetchSlots(selectedLotId);
    } catch (err: any) {
      setError(err.message || "Failed to start parking session.");
    }
  };

  const handleOpenCheckout = async () => {
    if (!activeSession || !selectedVehicle) return;
    setError("");
    setCheckoutLoading(true);
    setShowCheckout(true);

    try {
      // Simulate endpoint resolving checkout details
      // In a real system, the checkout calculated fees first, then starts transaction.
      // We call the checkout /end route which returns calculations
      // Let's call /end route directly:
      const data = await api.sessions.end({ qr_token: selectedVehicle.qr_token });
      
      // Calculate duration and fee locally since backend SessionResponse does not return them directly
      const entryTime = new Date(data.entry_time).getTime();
      const exitTime = new Date(data.actual_exit_time || new Date()).getTime();
      const durationMinutes = Math.max(1, Math.ceil((exitTime - entryTime) / 60000));
      const calculatedFee = (durationMinutes / 60) * 6.50;

      const augmentedData = {
        ...data,
        duration_minutes: durationMinutes,
        calculated_fee: calculatedFee
      };

      setCheckoutData(augmentedData);
    } catch (err: any) {
      setError(err.message || "Error resolving checkout transaction details.");
      setShowCheckout(false);
    } finally {
      setCheckoutLoading(false);
    }
  };

  const handlePayAndCompleteCheckout = async () => {
    setCheckoutLoading(true);
    try {
      // Simulation of secure payment processing
      await new Promise((resolve) => setTimeout(resolve, 2000));
      alert("Payment verified! Gateway transaction successful.");
      setShowCheckout(false);
      setCheckoutData(null);
      await checkActiveSession();
      if (selectedLotId) fetchSlots(selectedLotId);
    } catch (err: any) {
      alert("Payment failed. Please try again.");
    } finally {
      setCheckoutLoading(false);
    }
  };

  const handleExtendSession = async () => {
    if (!activeSession) return;
    setError("");
    try {
      await api.sessions.extend(activeSession.session_id, {
        additional_minutes: extendingMinutes
      });
      await checkActiveSession();
      alert("Session extension granted!");
    } catch (err: any) {
      setError(err.message || "Extension failed.");
    }
  };

  useEffect(() => {
    fetchInitialData();
  }, []);

  return (
    <div className="space-y-8 animate-slide-in">
      <div className="bg-slate-900/40 p-6 rounded-xl border border-white/5">
        <h1 className="text-3xl font-extrabold tracking-tight text-white">
          Parking <span className="text-accent-cyan neon-text-glow">Sessions</span>
        </h1>
        <p className="text-slate-400 text-sm mt-1">
          Perform check-in, monitor timers, and simulate check-outs with integrated payments
        </p>
      </div>

      {error && (
        <div className="flex items-center gap-2 bg-red-950/40 border border-red-500/30 text-red-400 px-4 py-3 rounded-lg text-sm">
          <ShieldAlert size={18} />
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <div className="text-slate-400 text-sm py-12 text-center glass-panel">Loading...</div>
      ) : activeSession ? (
        /* ================= ACTIVE SESSION DISPLAY ================= */
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="glass-panel p-6 space-y-6 relative overflow-hidden">
            {/* Pulsing indicator */}
            <div className="absolute top-6 right-6 w-3 h-3 bg-emerald-500 rounded-full animate-ping"></div>

            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Timer className="text-status-vacant" size={18} />
              Active Parking Session
            </h2>

            <div className="space-y-4">
              <div className="flex justify-between items-center text-sm border-b border-white/5 pb-2">
                <span className="text-slate-400">License Plate:</span>
                <span className="text-white font-bold font-mono text-base">{activeSession.license_plate}</span>
              </div>
              <div className="flex justify-between items-center text-sm border-b border-white/5 pb-2">
                <span className="text-slate-400">Assigned Slot:</span>
                <span className="text-white font-bold">{activeSession.slot_number}</span>
              </div>
              <div className="flex justify-between items-center text-sm border-b border-white/5 pb-2">
                <span className="text-slate-400">Entry Time (UTC):</span>
                <span className="text-white font-medium">{new Date(activeSession.entry_time).toLocaleTimeString()}</span>
              </div>
              <div className="flex justify-between items-center text-sm border-b border-white/5 pb-2">
                <span className="text-slate-400">Expected Departure (UTC):</span>
                <span className="text-white font-medium">{new Date(activeSession.predicted_departure).toLocaleTimeString()}</span>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className="text-slate-400">Remaining Duration:</span>
                <span className="text-accent-cyan font-bold">
                  {activeSession.remaining_minutes > 0 
                    ? `${Math.ceil(activeSession.remaining_minutes)} mins`
                    : "Expired (Violation status)"
                  }
                </span>
              </div>
            </div>

            <button
              onClick={handleOpenCheckout}
              className="w-full mt-4 flex items-center justify-center gap-2 bg-gradient-to-r from-rose-500 to-red-500 text-white font-bold py-3 px-4 rounded-lg hover:shadow-[0_0_15px_rgba(244,63,94,0.4)] transition-all text-sm"
            >
              <Square size={16} />
              Complete Parking & Checkout
            </button>
          </div>

          {/* Extend Session Panel */}
          <div className="glass-panel p-6 flex flex-col justify-between">
            <div>
              <h3 className="text-lg font-bold text-white border-b border-white/5 pb-4 mb-5 flex items-center gap-2">
                <RefreshCcw className="text-accent-cyan" size={18} />
                Extend Parking Session
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed mb-6">
                Need more time? Slide below to request additional parking minutes. Your reservation details and predicted departure time will update automatically.
              </p>

              <div>
                <label className="flex justify-between text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                  <span>Additional Duration:</span>
                  <span className="text-accent-cyan font-bold font-mono">{extendingMinutes} minutes</span>
                </label>
                <input
                  type="range"
                  min="10"
                  max="120"
                  step="10"
                  value={extendingMinutes}
                  onChange={(e) => setExtendingMinutes(parseInt(e.target.value))}
                  className="w-full accent-accent-cyan bg-slate-800 rounded-lg cursor-pointer h-2"
                />
              </div>
            </div>

            <button
              onClick={handleExtendSession}
              className="w-full flex items-center justify-center gap-2 bg-white/5 border border-white/10 hover:border-accent-cyan text-slate-300 hover:text-accent-cyan font-bold py-3 px-4 rounded-lg transition-all text-sm mt-8"
            >
              Request Extension
            </button>
          </div>
        </div>
      ) : (
        /* ================= START SESSION CHECK-IN FORM ================= */
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 glass-panel p-6">
            <h2 className="text-lg font-bold text-white border-b border-white/5 pb-4 mb-6 flex items-center gap-2">
              <Play className="text-status-vacant" size={18} />
              Start Parking Session (Check-in)
            </h2>

            <form onSubmit={handleStartSession} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                    Select Vehicle
                  </label>
                  <select
                    value={selectedVehicle?.id || ""}
                    onChange={(e) => {
                      const found = vehicles.find((v) => v.id === e.target.value);
                      if (found) setSelectedVehicle(found);
                    }}
                    className="w-full px-4 py-3 bg-[#0d1426]/80 border border-white/10 rounded-lg text-white focus:outline-none focus:border-accent-cyan transition-all text-sm font-semibold"
                  >
                    {vehicles.map((v) => (
                      <option key={v.id} value={v.id}>
                        {v.license_plate} ({v.vehicle_type})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                    Parking Lot
                  </label>
                  <select
                    value={selectedLotId}
                    onChange={(e) => {
                      setSelectedLotId(e.target.value);
                      fetchSlots(e.target.value);
                      fetchAiRecommendation(e.target.value);
                    }}
                    className="w-full px-4 py-3 bg-[#0d1426]/80 border border-white/10 rounded-lg text-white focus:outline-none focus:border-accent-cyan transition-all text-sm font-semibold"
                  >
                    {lots.map((l) => (
                      <option key={l.id} value={l.id}>
                        {l.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                  Select Parking Slot
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  {slots
                    .filter((s) => s.status === "VACANT")
                    .map((s) => (
                      <button
                        type="button"
                        key={s.id}
                        onClick={() => setSelectedSlotId(s.id)}
                        className={`p-3 rounded-lg border text-center font-bold font-mono text-xs transition-all ${
                          selectedSlotId === s.id
                            ? "bg-accent-cyan/15 border-accent-cyan text-accent-cyan shadow-[0_0_10px_rgba(0,242,254,0.2)]"
                            : "bg-slate-900/40 border-white/10 text-slate-400 hover:border-slate-500"
                        }`}
                      >
                        {s.slot_number} ({s.slot_type})
                      </button>
                    ))}
                </div>
              </div>

              <div>
                <label className="flex justify-between text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                  <span>Expected Parking Duration:</span>
                  <span className="text-accent-cyan font-bold font-mono">{expectedMinutes} minutes</span>
                </label>
                <input
                  type="range"
                  min="20"
                  max="240"
                  step="20"
                  value={expectedMinutes}
                  onChange={(e) => setExpectedMinutes(parseInt(e.target.value))}
                  className="w-full accent-accent-cyan bg-slate-800 rounded-lg cursor-pointer h-2"
                />
              </div>

              <button
                type="submit"
                className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-accent-blue to-accent-cyan text-slate-900 font-bold py-3.5 px-4 rounded-lg hover:shadow-[0_0_15px_rgba(0,242,254,0.5)] transition-all font-sans text-sm"
              >
                <Play size={16} />
                Scan Token & Start Session
              </button>
            </form>
          </div>

          {/* Right Side: AI Recommended Slot */}
          <div className="glass-panel p-6 h-fit space-y-4">
            <h3 className="text-lg font-bold text-white border-b border-white/5 pb-4 flex items-center gap-2">
              <Sparkles className="text-amber-400" size={18} />
              AI Recommendation
            </h3>
            {recommendedSlot ? (
              <div className="space-y-4">
                <p className="text-xs text-slate-400 leading-relaxed">
                  Our system analyzed lot occupancy patterns and predicts this slot has the lowest departure obstruction rate:
                </p>
                <div className="bg-amber-500/10 border border-amber-500/30 p-4 rounded-lg text-center">
                  <div className="text-[10px] uppercase tracking-wider font-bold text-amber-500">RECOMMENDED SLOT</div>
                  <div className="text-3xl font-black text-white font-mono mt-1">{recommendedSlot.slot_number}</div>
                  <div className="text-xs text-slate-300 font-semibold mt-1">Floor: {recommendedSlot.floor_level}</div>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    const slot = slots.find((s) => s.slot_number === recommendedSlot.slot_number);
                    if (slot) setSelectedSlotId(slot.id);
                  }}
                  className="w-full text-xs bg-amber-500/10 border border-amber-500/30 hover:bg-amber-500 hover:text-slate-900 text-amber-400 py-2 px-3 rounded-lg transition-all font-bold"
                >
                  Select This Slot
                </button>
              </div>
            ) : (
              <div className="text-xs text-slate-400 py-8 text-center">AI recommendations calculating...</div>
            )}
          </div>
        </div>
      )}

      {/* ================= PAYMENT CHECKOUT MODAL SIMULATOR ================= */}
      {showCheckout && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="glass-panel w-full max-w-md p-6 relative">
            <h3 className="text-xl font-bold text-white border-b border-white/5 pb-4 mb-4 flex items-center gap-2">
              <CreditCard className="text-accent-cyan" size={20} />
              Razorpay Checkout Simulation
            </h3>

            {checkoutLoading ? (
              <div className="flex flex-col items-center justify-center py-12 space-y-4">
                <div className="w-12 h-12 border-4 border-accent-cyan border-t-transparent rounded-full animate-spin"></div>
                <div className="text-sm text-slate-300">Processing secure transaction...</div>
              </div>
            ) : checkoutData ? (
              <div className="space-y-4 py-2">
                <div className="flex justify-between items-center text-sm border-b border-white/5 pb-2">
                  <span className="text-slate-400">Parking Slot:</span>
                  <span className="text-white font-bold">{checkoutData.slot_number}</span>
                </div>
                <div className="flex justify-between items-center text-sm border-b border-white/5 pb-2">
                  <span className="text-slate-400">Total Duration:</span>
                  <span className="text-white font-bold">{checkoutData.duration_minutes} minutes</span>
                </div>
                <div className="flex justify-between items-center text-sm border-b border-white/5 pb-2">
                  <span className="text-slate-400">Charge Rate:</span>
                  <span className="text-white font-bold">$6.50 / hour</span>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="text-slate-400">Grand Total Fee:</span>
                  <span className="text-status-vacant font-black text-lg">${checkoutData.calculated_fee.toFixed(2)}</span>
                </div>

                <div className="flex gap-3 pt-6">
                  <button
                    onClick={() => setShowCheckout(false)}
                    className="flex-1 bg-white/5 hover:bg-white/10 text-slate-300 font-bold py-2.5 px-4 rounded-lg text-sm transition-all"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handlePayAndCompleteCheckout}
                    className="flex-1 bg-gradient-to-r from-accent-blue to-accent-cyan text-slate-900 font-bold py-2.5 px-4 rounded-lg text-sm hover:shadow-[0_0_10px_rgba(0,242,254,0.4)] transition-all"
                  >
                    Pay ${checkoutData.calculated_fee.toFixed(2)}
                  </button>
                </div>
              </div>
            ) : (
              <div className="text-sm text-slate-300 text-center py-8">Resolving check-out...</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
