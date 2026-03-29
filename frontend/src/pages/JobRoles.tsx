import React, { useState, useEffect } from "react";
import { 
  Briefcase, 
  Plus, 
  Search, 
  Filter, 
  MoreVertical, 
  Edit2, 
  Trash2, 
  Building,
  History,
  Info,
  ChevronRight
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { SidebarInset } from "@/components/ui/sidebar";
import { toast } from "sonner";
import { useWebSocket } from "@/hooks/useWebSocket";
import { useDepartments } from "@/hooks/useDepartments";
import { format } from "date-fns";
import { es } from "date-fns/locale";

interface JobRole {
  id: string;
  name: string;
  description: string;
  department: string;
  created_at: string;
  updated_at: string;
  created_by_info?: { email: string };
  updated_by_info?: { email: string };
  department_info?: { name: string };
}

export default function JobRoles() {
  const [roles, setRoles] = useState<JobRole[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [deptFilter, setDeptFilter] = useState("all");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingRole, setEditingRole] = useState<JobRole | null>(null);
  
  // Form State
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    department: ""
  });

  // Hook reutilizable de departamentos (espera conexión abierta antes de pedir datos)
  const { departments } = useDepartments();

  // WebSocket para Cargos (dinámico para redes locales)
  const wsHostname = typeof window !== 'undefined' ? window.location.hostname : 'localhost';
  const { lastMessage, sendMessage, readyState } = useWebSocket(`ws://${wsHostname}:8000/ws/job-role-management/`);

  useEffect(() => {
    if (readyState === 1) { // OPEN
      sendMessage({ action: "list" });
    }
  }, [readyState]);

  // Manejar mensajes entrantes del WebSocket de Cargos
  useEffect(() => {
    if (!lastMessage) return;
    if (lastMessage.status === "success") {
      if (lastMessage.action === "list") {
        setRoles(lastMessage.data);
      } else if (lastMessage.action === "create") {
        setRoles(prev => [...prev, lastMessage.data]);
        toast.success("Cargo creado exitosamente");
        closeModal();
      } else if (lastMessage.action === "update") {
        setRoles(prev => prev.map(r => r.id === lastMessage.data.id ? lastMessage.data : r));
        toast.success("Cargo actualizado correctamente");
        closeModal();
      } else if (lastMessage.action === "delete") {
        setRoles(prev => prev.filter(r => r.id !== lastMessage.data));
        toast.success("Cargo eliminado (soft delete)");
      }
    } else if (lastMessage.event) {
      if (lastMessage.event === "job_role_created") {
        setRoles(prev => [...prev.filter(r => r.id !== lastMessage.data.id), lastMessage.data]);
      } else if (lastMessage.event === "job_role_updated") {
        setRoles(prev => prev.map(r => r.id === lastMessage.data.id ? lastMessage.data : r));
      } else if (lastMessage.event === "job_role_deleted") {
        setRoles(prev => prev.filter(r => r.id !== lastMessage.data.id));
      }
    } else if (lastMessage.status === "error") {
      try {
        const errorObj = JSON.parse(lastMessage.message);
        const messages = Object.entries(errorObj).map(([key, value]) => `${key}: ${value}`).join(", ");
        toast.error(`Error: ${messages}`);
      } catch {
        toast.error(lastMessage.message || "Error en la operación");
      }
    }
  }, [lastMessage]);

  const openModal = (role: JobRole | null = null) => {
    if (role) {
      setEditingRole(role);
      setFormData({
        name: role.name,
        description: role.description || "",
        department: role.department
      });
    } else {
      setEditingRole(null);
      setFormData({ name: "", description: "", department: "" });
    }
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingRole(null);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.department) {
        toast.error("Debes seleccionar un departamento");
        return;
    }
    if (editingRole) {
      sendMessage({
        action: "update",
        data: { id: editingRole.id, ...formData }
      });
    } else {
      sendMessage({
        action: "create",
        data: formData
      });
    }
  };

  const handleDelete = (id: string) => {
    if (window.confirm("¿Estás seguro de eliminar este cargo?")) {
      sendMessage({ action: "delete", data: { id } });
    }
  };

  const filteredRoles = roles.filter(role => {
    const matchesSearch = role.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         role.department_info?.name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesDept = deptFilter === "all" || role.department === deptFilter;
    return matchesSearch && matchesDept;
  });

  return (
    <SidebarInset>
      <header className="flex h-16 shrink-0 items-center justify-between px-6 border-b glassmorphism sticky top-0 z-20">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Building className="h-4 w-4" />
          <ChevronRight className="h-4 w-4" />
          <Briefcase className="h-4 w-4 text-primary" />
          <span className="font-medium text-foreground">Gestión de Cargos</span>
        </div>
      </header>

      <main className="p-6 space-y-6 animate-in fade-in duration-500">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Cargos</h1>
            <p className="text-muted-foreground">Define y administra las posiciones laborales por departamento.</p>
          </div>
          <Button onClick={() => openModal()} className="gradient-primary hover-lift">
            <Plus className="mr-2 h-4 w-4" /> Nuevo Cargo
          </Button>
        </div>

        <Card className="border-none shadow-xl bg-card/50 backdrop-blur-sm">
          <CardHeader className="pb-3">
            <div className="flex flex-col md:flex-row gap-4 items-center">
              <div className="relative flex-1 w-full">
                <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input 
                  placeholder="Buscar cargo o departamento..." 
                  className="pl-10 h-10"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
              <div className="flex items-center gap-2 w-full md:w-auto">
                <Filter className="h-4 w-4 text-muted-foreground" />
                <Select value={deptFilter} onValueChange={setDeptFilter}>
                  <SelectTrigger className="w-[200px]">
                    <SelectValue placeholder="Filtrar por Depto." />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Todos los Deptos.</SelectItem>
                    {departments.map((d) => (
                      <SelectItem key={d.id} value={d.id}>{d.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="rounded-md border border-muted/20">
              <Table>
                <TableHeader className="bg-muted/30">
                  <TableRow>
                    <TableHead className="font-bold">Nombre del Cargo</TableHead>
                    <TableHead className="font-bold">Departamento</TableHead>
                    <TableHead className="font-bold">Fecha Creación</TableHead>
                    <TableHead className="font-bold">Creado Por</TableHead>
                    <TableHead className="text-right">Acciones</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredRoles.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={5} className="h-32 text-center text-muted-foreground">
                        No se encontraron cargos. {searchTerm && "Prueba con otra búsqueda."}
                      </TableCell>
                    </TableRow>
                  ) : (
                    filteredRoles.map((role) => (
                      <TableRow key={role.id} className="hover:bg-muted/10 transition-colors group">
                        <TableCell className="font-medium">
                          <div className="flex flex-col">
                            <span>{role.name}</span>
                            {role.description && (
                              <span className="text-xs text-muted-foreground line-clamp-1">{role.description}</span>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="secondary" className="bg-blue-500/10 text-blue-500 hover:bg-blue-500/20">
                            {role.department_info?.name || "N/A"}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-muted-foreground text-sm">
                          {format(new Date(role.created_at), "dd MMM, yyyy", { locale: es })}
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <div className="w-6 h-6 rounded-full bg-primary/20 flex items-center justify-center text-[10px] font-bold text-primary">
                              {role.created_by_info?.email[0].toUpperCase()}
                            </div>
                            <span className="text-xs">{role.created_by_info?.email.split('@')[0]}</span>
                          </div>
                        </TableCell>
                        <TableCell className="text-right">
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" className="h-8 w-8 p-0">
                                <MoreVertical className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end" className="w-40 glassmorphism">
                              <DropdownMenuItem onClick={() => openModal(role)}>
                                <Edit2 className="mr-2 h-4 w-4" /> Editar
                              </DropdownMenuItem>
                              <DropdownMenuItem 
                                onClick={() => handleDelete(role.id)}
                                className="text-red-500 focus:text-red-500"
                              >
                                <Trash2 className="mr-2 h-4 w-4" /> Eliminar
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      </main>

      {/* Modal de Creación/Edición */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent className="sm:max-w-[500px] glassmorphism border-none shadow-2xl">
          <DialogHeader>
            <DialogTitle className="text-2xl font-bold flex items-center gap-2">
              <Briefcase className="h-5 w-5 text-primary" />
              {editingRole ? "Editar Cargo" : "Nuevo Cargo"}
            </DialogTitle>
            <DialogDescription>
              {editingRole ? "Modifica los detalles del cargo actual." : "Crea una nueva posición laboral especificando su departamento."}
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-6 pt-4">
            <div className="space-y-2">
              <Label htmlFor="department">Departamento <span className="text-red-500">*</span></Label>
              <Select 
                value={formData.department} 
                onValueChange={(v) => setFormData({...formData, department: v})}
              >
                <SelectTrigger id="department">
                  <SelectValue placeholder="Selecciona un departamento" />
                </SelectTrigger>
                <SelectContent>
                  {departments.map((d) => (
                    <SelectItem key={d.id} value={d.id}>{d.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="name">Nombre del Cargo <span className="text-red-500">*</span></Label>
              <Input 
                id="name" 
                placeholder="Ej. Desarrollador Senior" 
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="description">Descripción (Opcional)</Label>
              <Textarea 
                id="description" 
                placeholder="Describe las responsabilidades..." 
                className="resize-none h-24"
                value={formData.description}
                onChange={(e) => setFormData({...formData, description: e.target.value})}
              />
            </div>
            
            {editingRole && (
               <Card className="bg-muted/30 border-none">
                 <CardContent className="p-4 flex flex-col gap-2">
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <History className="h-3 w-3" />
                        <span>Historial de Auditoría</span>
                    </div>
                    <div className="grid grid-cols-2 gap-4 text-[11px]">
                        <div>
                            <span className="block font-bold">Creado el</span>
                            <span>{format(new Date(editingRole.created_at), "PPP p", { locale: es })}</span>
                        </div>
                        <div>
                             <span className="block font-bold">Por</span>
                             <span>{editingRole.created_by_info?.email}</span>
                        </div>
                    </div>
                 </CardContent>
               </Card>
            )}

            <DialogFooter className="gap-2 sm:gap-0">
              <Button type="button" variant="ghost" onClick={closeModal}>
                Cancelar
              </Button>
              <Button type="submit" className="gradient-primary">
                {editingRole ? "Guardar Cambios" : "Crear Cargo"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </SidebarInset>
  );
}
