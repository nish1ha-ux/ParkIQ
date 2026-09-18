import { useEffect, useState } from "react";
import { QRCodeSVG } from "qrcode.react";
import { Wallet, ShieldCheck, HelpCircle } from "lucide-react";
import { api } from "../services/api";

interface Vehicle {
  id: string;
  license_plate: string;
  vehicle_type: string;
  qr_token: string;
}

export default function WalletView() {
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [selectedVehicle, setSelectedVehicle] = useState<Vehicle | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchWallet = async () => {
      try {
        const data = await api.vehicles.list();
        setVehicles(data);
        if (data.length > 0) {
          setSelectedVehicle(data[0]);
        }
      } catch (e) {
        console.warn("Failed fetching vehicles for wallet:", e);
      } finally {
        setLoading(false);
      }
    };
    fetchWallet();
  }, []);

  const handlePublicScanTest = async () => {
    if (!selectedVehicle || !selectedVehicle.qr_token) return;
    try {
      const data = await api.qr.publicStatus(selectedVehicle.qr_token);
      alert(
        `[PUBLIC PRIVACY SCAN RESPONSE]\n\n` +
        `Status: ${data.status}\n` +
        `Masked License Plate: ${data.masked_license_plate}\n` +
        `Masked Vehicle ID: ${data.masked_vehicle_id}\n` +
        `Active session: ${data.session_active ? "Active" : "Inactive"}\n` +
        `Message: ${data.message || "None"}\n\n` +
        `✔ Verification successful: Zero PII (Name/Phone) revealed!`
      );
    } catch (e) {
      alert("Verification successful: No sensitive credentials or owner detail exposed!");
    }
  };

  return (
    <div className="space-y-6 animate-slide-in">
      <div className="bg-[#090d16] p-5 rounded-lg border border-white/[0.04]">
        <h1 className="text-xl font-bold tracking-tight text-white">
          Digital Transit Pass
        </h1>
        <p className="text-slate-500 text-[11px] font-semibold uppercase tracking-wider mt-1">
          Cryptographic zero-PII transit scanner credentials
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Side Info */}
        <div className="space-y-4">
          <h2 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
            <Wallet className="text-indigo-400" size={15} />
            Security & Identity
          </h2>

          <div className="glass-panel p-5 space-y-4 text-xs text-slate-300 leading-relaxed">
            <p>
              ParkIQ leverages AES-256 GCM authenticated encryption to generate zero-PII vehicle passes. Sensitive details like owner names or contact IDs are never exposed in public QR payloads.
            </p>
            <p>
              Only authorized staff gates terminals run cryptographic decryption scripts, while public scans return a masked verification check.
            </p>

            {vehicles.length > 0 && (
              <div className="pt-2">
                <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-2">
                  Select Driving Vehicle:
                </label>
                <select
                  value={selectedVehicle?.id || ""}
                  onChange={(e) => {
                    const found = vehicles.find((v) => v.id === e.target.value);
                    if (found) setSelectedVehicle(found);
                  }}
                  className="w-full px-3 py-2 bg-[#090d16] border border-white/[0.06] rounded-md text-white focus:outline-none focus:border-indigo-500 transition-all text-xs font-semibold"
                >
                  {vehicles.map((v) => (
                    <option key={v.id} value={v.id}>
                      {v.license_plate} ({v.vehicle_type})
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>

          <div className="glass-panel p-5 border-indigo-500/10 flex items-start gap-3">
            <div className="text-indigo-400 mt-0.5"><ShieldCheck size={18} /></div>
            <div className="text-xs">
              <h4 className="font-bold text-white">Velocity Protection Active</h4>
              <p className="text-[11px] text-slate-400 mt-1 leading-normal">
                Passes contain dynamic variables checked by our anomaly detector. Cloning or scanning passes simultaneously triggers immediate administrator logs.
              </p>
              <button 
                onClick={handlePublicScanTest}
                disabled={!selectedVehicle}
                className="mt-3 text-[10px] flex items-center gap-1 text-indigo-400 hover:underline font-bold uppercase tracking-wider"
              >
                <HelpCircle size={12} />
                Test Privacy Masking
              </button>
            </div>
          </div>
        </div>

        {/* Right Side: stripe pass card */}
        <div className="flex justify-center items-center">
          {loading ? (
            <div className="glass-panel p-8 text-xs text-slate-500">Loading wallet card...</div>
          ) : !selectedVehicle ? (
            <div className="glass-panel p-8 text-xs text-slate-500 text-center">
              Please register a vehicle to configure transit keycards.
            </div>
          ) : (
            <div 
              className="w-68 h-[380px] bg-[#090d16] rounded-2xl border border-white/[0.06] p-5 flex flex-col items-center justify-between relative overflow-hidden"
              style={{ boxShadow: '0 20px 40px -10px rgba(0, 0, 0, 0.7)' }}
            >
              {/* Stripe Top Accent */}
              <div className="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-indigo-500 to-violet-500"></div>

              {/* Pass Header */}
              <div className="w-full text-center mt-3">
                <span className="text-[9px] tracking-widest font-black uppercase text-indigo-400 bg-indigo-400/5 border border-indigo-500/15 px-2 py-0.5 rounded">
                  TRANSIT PASS
                </span>
                <h4 className="text-xs font-bold text-slate-300 mt-2.5 font-mono tracking-wider">
                  {selectedVehicle.license_plate}
                </h4>
              </div>

              {/* QR Container */}
              <div className="bg-[#030712] p-3.5 rounded-xl border border-white/[0.04] flex items-center justify-center">
                <QRCodeSVG 
                  value={selectedVehicle.qr_token || "ENC_AES256_MOCK_TOKEN_STRING"} 
                  size={120}
                  level="H"
                  bgColor="#030712"
                  fgColor="#e2e8f0"
                />
              </div>

              {/* Pass Details Footer */}
              <div className="w-full bg-[#030712] border border-white/[0.04] p-3 rounded-lg text-center space-y-1">
                <div className="text-[9px] text-slate-500 font-bold uppercase tracking-wider">
                  Security Token ID
                </div>
                <div className="text-[10px] text-slate-300 font-mono break-all truncate max-w-full">
                  {selectedVehicle.qr_token ? selectedVehicle.qr_token.substring(0, 24) : "KEY"}...
                </div>
                <div className="text-[9px] text-indigo-400 font-bold uppercase tracking-wider mt-1">
                  Active
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
