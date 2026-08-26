import { useState, type SyntheticEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../authStore';
import { Mail, Lock, User, AlertCircle } from 'lucide-react';


export function AuthPage() {
  const [isLogin, setIsLogin] = useState(true);

  // Form States
  const [username, setUsername] = useState(''); // Für Register
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const login = useAuthStore((state) => state.login);
  const navigate = useNavigate();

  const handleLogin = async (e: SyntheticEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const response = await fetch("http://localhost:8000/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({
          email: email,
          password: password
        })
            })


      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || 'Ungültige Anmeldedaten');
      }
      const data = await response.json()
      console.log("Backend-Antwort beim Login:", data); // Kurz prüfen!
      login({ email });

      navigate('/');
    } catch (err: any) {
      setError(err.message || 'Ein Fehler ist aufgetreten');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: SyntheticEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const response = await fetch('http://localhost:8000/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: "include",
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Registrierung fehlgeschlagen');
      }


      login({ email });

      navigate('/');
    } catch (err: any) {
      setError(err.message || 'Ein Fehler ist aufgetreten');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div 
      className="min-h-screen w-full flex items-center justify-center p-4 bg-cover bg-center bg-no-repeat relative font-sans"
      style={{
      backgroundImage: `url('/background.jpg')`, // Pfad zu deinem Bild im public-Ordner
    }}
    >
      {/* Dunkles Overlay für besseren Kontrast */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-[2px]"></div>

      {/* Glassmorphism Card */}
      <div className="w-full max-w-[400px] bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl p-8 shadow-[0_8px_32px_0_rgba(0,0,0,0.37)] relative z-10 text-white">
        
        {/* Titel */}
        <h1 className="text-3xl font-bold text-center mb-8 tracking-wide">
          {isLogin ? 'Login' : 'Registration'}
        </h1>

        {/* Fehlermeldung */}
        {error && (
          <div className="mb-6 p-3 bg-red-500/20 border border-red-500/30 rounded-lg flex items-center gap-2 text-red-200 text-xs">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Formular */}
        <form onSubmit={isLogin ? handleLogin : handleRegister} className="space-y-6">
 
          

          {/* Email Input */}
          <div className="relative border-b border-white/60 focus-within:border-white transition-all pb-1">
            <label className="block text-xs font-light text-slate-200">Email</label>
            <div className="flex items-center justify-between mt-1">
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="codehal@gmail.com"
                className="w-full bg-transparent text-sm text-white focus:outline-none placeholder-slate-400/60 pr-2"
              />
              <Mail className="w-4 h-4 text-white/80 shrink-0" />
            </div>
          </div>

          {/* Password Input */}
          <div className="relative border-b border-white/60 focus-within:border-white transition-all pb-1">
            <label className="block text-xs font-light text-slate-200">Password</label>
            <div className="flex items-center justify-between mt-1">
              <input
                type="password"
                required
                minLength={6}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full bg-transparent text-sm text-white focus:outline-none placeholder-slate-400/60 pr-2"
              />
              <Lock className="w-4 h-4 text-white/80 shrink-0" />
            </div>
          </div>

          {/* Remember Me & Forgot Password (Nur bei Login) */}
          {isLogin && (
            <div className="flex items-center justify-between text-xs font-light text-slate-200 pt-1">
              <label className="flex items-center gap-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="rounded border-white/40 bg-white/10 text-white focus:ring-0 w-3.5 h-3.5 accent-purple-500"
                />
                <span>Remember me</span>
              </label>
              <a href="#" className="hover:underline text-slate-200">
                Forgot Password?
              </a>
            </div>
          )}

          {/* Abgerundeter, weißer Button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-white hover:bg-slate-100 disabled:opacity-50 text-slate-900 font-semibold py-2.5 rounded-full transition-all duration-200 shadow-md text-sm mt-4"
          >
            {loading ? 'Processing...' : isLogin ? 'Login' : 'Register'}
          </button>
        </form>

        {/* Footer Wechsel-Link */}
        <div className="text-center mt-6 text-xs text-slate-200 font-light">
          {isLogin ? (
            <p>
              Don't have an account?{' '}
              <button
                type="button"
                onClick={() => {
                  setIsLogin(false);
                  setError(null);
                }}
                className="font-bold hover:underline ml-1 text-white"
              >
                Register
              </button>
            </p>
          ) : (
            <p>
              Already have an account?{' '}
              <button
                type="button"
                onClick={() => {
                  setIsLogin(true);
                  setError(null);
                }}
                className="font-bold hover:underline ml-1 text-white"
              >
                Login
              </button>
            </p>
          )}
        </div>

      </div>
    </div>
  );
}