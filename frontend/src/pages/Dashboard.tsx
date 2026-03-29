import React, { useEffect, useState } from "react";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/components/ui/card";
import { 
  SidebarProvider, 
  Sidebar, 
  SidebarContent, 
  SidebarHeader, 
  SidebarGroup, 
  SidebarGroupLabel, 
  SidebarGroupContent, 
  SidebarMenu, 
  SidebarMenuItem, 
  SidebarMenuButton,
  SidebarTrigger,
  SidebarInset,
} from "@/components/ui/sidebar";
import { 
  Users, 
  LayoutDashboard, 
  FileText, 
  Settings, 
  LogOut, 
  Bell, 
  Search,
  TrendingUp,
  UserCheck,
  Calendar,
  Building,
  Briefcase
} from "lucide-react";
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  AreaChart,
  Area
} from "recharts";
import { toast } from "sonner";
import { Input } from "@/components/ui/input";

const data = [
  { name: "Lun", value: 400 },
  { name: "Mar", value: 300 },
  { name: "Mié", value: 600 },
  { name: "Jue", value: 800 },
  { name: "Vie", value: 500 },
  { name: "Sáb", value: 900 },
  { name: "Dom", value: 1000 },
];

import { useWebSocket } from "@/hooks/useWebSocket";

export const DashboardContent = () => {
  const { user, logout } = useAuth();
  const [realTimeMsg, setRealTimeMsg] = useState("Sincronizando con el servidor...");
  
  // Conexión real a WebSockets para notificaciones (dinámico para red local)
  const wsHostname = typeof window !== 'undefined' ? window.location.hostname : 'localhost';
  const { lastMessage, readyState } = useWebSocket(user ? `ws://${wsHostname}:8000/ws/users/` : null);

  useEffect(() => {
    if (readyState === WebSocket.OPEN) {
      setRealTimeMsg("Conectado en tiempo real 🟢");
    } else if (readyState === WebSocket.CONNECTING) {
      setRealTimeMsg("Conectando...");
    } else {
      setRealTimeMsg("Desconectado de notificaciones 🔴");
    }
  }, [readyState]);

  useEffect(() => {
    if (lastMessage) {
      toast.info(`Nueva notificación: ${lastMessage.message || "Actividad detectada"}`);
    }
  }, [lastMessage]);

  return (
    <SidebarInset>
      <header className="flex h-16 shrink-0 items-center justify-between px-6 border-b glassmorphism sticky top-0 z-20">
        <div className="flex items-center gap-4">
          <SidebarTrigger />
          <div className="relative w-64 hidden md:block">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input placeholder="Buscar..." className="pl-10 h-9 bg-muted/50 border-none" />
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" className="relative">
            <Bell className="h-5 w-5" />
            <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full border-2 border-background" />
          </Button>
          <div className="flex items-center gap-3 pl-4 border-l">
            <div className="flex flex-col items-end hidden sm:flex">
              <span className="text-sm font-medium">{user?.email}</span>
              <span className="text-xs text-muted-foreground uppercase font-bold tracking-tighter">Administrador</span>
            </div>
            <div className="h-9 w-9 rounded-full bg-gradient-to-br from-primary to-blue-600 flex items-center justify-center text-white font-bold">
              {user?.email[0].toUpperCase()}
            </div>
          </div>
        </div>
      </header>

      <main className="p-6 space-y-8 animate-in fade-in duration-500">
        <div className="flex flex-col gap-2">
          <h1 className="text-3xl font-bold tracking-tight">Bienvenido de nuevo 👋</h1>
          <p className="text-muted-foreground">{realTimeMsg}</p>
        </div>

        {/* Stats Grid */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card className="hover-lift">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Total Empleados</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">124</div>
              <p className="text-xs text-green-500 flex items-center gap-1 mt-1">
                <TrendingUp className="h-3 w-3" /> +12% desde el mes pasado
              </p>
            </CardContent>
          </Card>
          <Card className="hover-lift">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Activos Ahora</CardTitle>
              <UserCheck className="h-4 w-4 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">89</div>
              <p className="text-xs text-muted-foreground mt-1">
                72% de la plantilla actual
              </p>
            </CardContent>
          </Card>
          <Card className="hover-lift">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Nóminas Generadas</CardTitle>
              <FileText className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">$1.2M</div>
              <p className="text-xs text-muted-foreground mt-1">
                Periodo: Marzo 2026
              </p>
            </CardContent>
          </Card>
          <Card className="hover-lift">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Próximos Eventos</CardTitle>
              <Calendar className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">5</div>
              <p className="text-xs text-blue-500 mt-1">
                Revisiones pendientes esta semana
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Charts & Activity */}
        <div className="grid gap-6 md:grid-cols-7">
          <Card className="md:col-span-4 overflow-hidden border-none shadow-xl bg-slate-900 text-white">
            <CardHeader>
              <CardTitle>Rendimiento del Sistema</CardTitle>
              <CardDescription className="text-slate-400">Actividad de usuarios en tiempo real</CardDescription>
            </CardHeader>
            <CardContent className="h-[300px] p-0 pr-4">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data}>
                  <defs>
                    <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#1e293b" />
                  <XAxis dataKey="name" stroke="#64748b" axisLine={false} tickLine={false} dy={10} />
                  <YAxis stroke="#64748b" axisLine={false} tickLine={false} dx={-10} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: "#0f172a", border: "none", borderRadius: "8px", boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.1)" }}
                    itemStyle={{ color: "#3b82f6" }}
                  />
                  <Area type="monotone" dataKey="value" stroke="#3b82f6" strokeWidth={3} fillOpacity={1} fill="url(#colorValue)" />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card className="md:col-span-3 hover-lift">
            <CardHeader>
              <CardTitle>Actividad Reciente</CardTitle>
              <CardDescription>Eventos registrados por el sistema</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-full bg-muted flex items-center justify-center">
                      <Users className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <div className="flex-1 space-y-1">
                      <p className="text-sm font-medium leading-none">Nuevo empleado registrado</p>
                      <p className="text-xs text-muted-foreground">Hace {i * 15} minutos</p>
                    </div>
                    <div className="text-xs font-bold text-green-500 bg-green-500/10 px-2 py-1 rounded">EXITO</div>
                  </div>
                ))}
              </div>
              <Button variant="outline" className="w-full mt-6">Ver Todo</Button>
            </CardContent>
          </Card>
        </div>
      </main>
    </SidebarInset>
  );
};

import { Outlet, Link, useLocation } from "react-router-dom";

export default function Dashboard() {
  const { logout } = useAuth();
  const location = useLocation();
  
  return (
    <SidebarProvider>
      <div className="flex min-h-screen w-full bg-background">
        <Sidebar collapsible="icon" className="border-r">
          <SidebarHeader className="p-4 border-b">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg gradient-primary flex items-center justify-center text-white font-bold">N</div>
              <span className="font-bold whitespace-nowrap group-data-[collapsible=icon]:hidden">NominaRRHH</span>
            </div>
          </SidebarHeader>
          <SidebarContent>
            <SidebarGroup>
              <SidebarGroupLabel className="group-data-[collapsible=icon]:hidden">Principal</SidebarGroupLabel>
              <SidebarGroupContent>
                <SidebarMenu>
                  <SidebarMenuItem>
                    <SidebarMenuButton asChild isActive={location.pathname === "/dashboard"} tooltip="Panel Principal">
                      <Link to="/dashboard">
                        <LayoutDashboard className="h-4 w-4" />
                        <span>Dashboard</span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                  <SidebarMenuItem>
                    <SidebarMenuButton asChild isActive={location.pathname === "/dashboard/users"} tooltip="Gestión de Empleados">
                      <Link to="/dashboard/users">
                        <Users className="h-4 w-4" />
                        <span>Empleados</span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                  <SidebarMenuItem>
                    <SidebarMenuButton asChild isActive={location.pathname === "/dashboard/departments"} tooltip="Gestión de Departamentos">
                      <Link to="/dashboard/departments">
                        <Building className="h-4 w-4" />
                        <span>Departamentos</span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                  <SidebarMenuItem>
                    <SidebarMenuButton asChild isActive={location.pathname === "/dashboard/job-roles"} tooltip="Gestión de Cargos">
                      <Link to="/dashboard/job-roles">
                        <Briefcase className="h-4 w-4" />
                        <span>Cargos</span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                  <SidebarMenuItem>
                    <SidebarMenuButton tooltip="Contratos y Nóminas">
                      <FileText className="h-4 w-4" />
                      <span>Nóminas</span>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>

            <SidebarGroup>
              <SidebarGroupLabel className="group-data-[collapsible=icon]:hidden">Configuración</SidebarGroupLabel>
              <SidebarGroupContent>
                <SidebarMenu>
                  <SidebarMenuItem>
                    <SidebarMenuButton tooltip="Preferencias">
                      <Settings className="h-4 w-4" />
                      <span>Ajustes</span>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                  <SidebarMenuItem>
                    <SidebarMenuButton onClick={logout} className="text-red-500 hover:text-red-600 hover:bg-red-50/50" tooltip="Cerrar Sesión">
                      <LogOut className="h-4 w-4" />
                      <span>Cerrar Sesión</span>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>
          </SidebarContent>
        </Sidebar>

        <Outlet />
      </div>
    </SidebarProvider>
  );
}
