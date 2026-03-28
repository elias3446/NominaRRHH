import { RegisterForm } from "@/components/auth/RegisterForm";
import { useAuth } from "@/hooks/useAuth";
import { Navigate } from "react-router-dom";

const Register = () => {
  const { user } = useAuth();

  if (user) return <Navigate to="/dashboard" />;

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4 relative overflow-hidden">
      {/* Elementos decorativos de fondo */}
      <div className="absolute -top-10 -right-10 w-80 h-80 bg-primary/10 rounded-full blur-3xl animate-pulse" />
      <div className="absolute -bottom-10 -left-10 w-96 h-96 bg-blue-400/10 rounded-full blur-3xl animate-pulse delay-700" />
      
      <div className="w-full max-w-md z-10 space-y-8">
        <div className="text-center space-y-2">
          <h1 className="text-4xl font-extrabold tracking-tight text-gradient">Únete a Nosotros</h1>
          <p className="text-muted-foreground">Comienza a gestionar tu equipo de forma eficiente</p>
        </div>
        
        <RegisterForm />
      </div>
    </div>
  );
};

export default Register;
