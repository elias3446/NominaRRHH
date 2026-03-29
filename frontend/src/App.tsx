import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes, Navigate } from "react-router-dom";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { AuthProvider, useAuth } from "@/hooks/useAuth";
import Index from "./pages/Index.tsx";
import Register from "./pages/Register.tsx";
import Dashboard, { DashboardContent } from "./pages/Dashboard.tsx";
import NotFound from "./pages/NotFound.tsx";

import Users from "./pages/Users.tsx";
import Departments from "./pages/Departments.tsx";
import JobRoles from "./pages/JobRoles.tsx";

const queryClient = new QueryClient();

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { user, loading } = useAuth();
  
  if (loading) return <div className="flex h-screen items-center justify-center">Cargando...</div>;
  if (!user) return <Navigate to="/" />;
  
  return <>{children}</>;
};

import { SessionGuard } from "@/components/auth/SessionGuard";

const App = () => (
  <QueryClientProvider client={queryClient}>
    <AuthProvider>
      <SessionGuard>
        <TooltipProvider>
          <Toaster />
          <Sonner />
          <BrowserRouter>
            <Routes>
              <Route path="/" element={<Index />} />
              <Route path="/register" element={<Register />} />
              <Route 
                path="/dashboard" 
                element={
                  <ProtectedRoute>
                    <Dashboard />
                  </ProtectedRoute>
                } 
              >
                <Route index element={<DashboardContent />} />
                <Route path="users" element={<Users />} />
                <Route path="departments" element={<Departments />} />
                <Route path="job-roles" element={<JobRoles />} />
              </Route>
              <Route path="*" element={<NotFound />} />
            </Routes>
          </BrowserRouter>
        </TooltipProvider>
      </SessionGuard>
    </AuthProvider>
  </QueryClientProvider>
);

export default App;
