import { LoginForm } from "@/components/auth/LoginForm";
import { useAuth } from "@/hooks/useAuth";
import { Navigate } from "react-router-dom";

const Index = () => {
  const { user } = useAuth();

  // Redirigir si ya está autenticado
  if (user) return <Navigate to="/dashboard" />;

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4 relative overflow-hidden">
      {/* Elementos decorativos de fondo */}
      <div className="absolute top-0 -left-4 w-72 h-72 bg-primary/10 rounded-full blur-3xl animate-pulse" />
      <div className="absolute bottom-0 -right-4 w-96 h-96 bg-blue-400/10 rounded-full blur-3xl animate-pulse delay-1000" />
      
      <div className="w-full max-w-md z-10 space-y-8">
        <div className="text-center space-y-2">
          <h1 className="text-4xl font-extrabold tracking-tight text-gradient">NominaRRHH</h1>
          <p className="text-muted-foreground">Sistema Integral de Gestión de Recursos Humanos</p>
        </div>
        
        <LoginForm />
        
        <p className="text-center text-xs text-muted-foreground px-8">
          Al continuar, aceptas nuestros Términos de Servicio y Política de Privacidad.
        </p>
      </div>
    </div>
  );
};

export default Index;
