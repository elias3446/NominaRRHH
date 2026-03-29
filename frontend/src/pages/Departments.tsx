import { useState, useEffect, useMemo } from "react";
import { Department } from "@/types/department";
import { useWebSocket } from "@/hooks/useWebSocket";
import { 
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow 
} from "@/components/ui/table";
import { 
  Dialog, DialogContent, DialogHeader, DialogTitle 
} from "@/components/ui/dialog";
import { 
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, 
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle 
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { DepartmentForm } from "@/components/department-management/DepartmentForm";
import { Edit, Trash2, Building, Search, Info } from "lucide-react";
import { toast } from "sonner";
import { 
  Tooltip, TooltipContent, TooltipProvider, TooltipTrigger 
} from "@/components/ui/tooltip";

// Get dynamic WS URL for local network support
const getWsUrl = () => {
  const hostname = typeof window !== 'undefined' ? window.location.hostname : 'localhost';
  const backendHost = import.meta.env.VITE_API_URL 
    ? new URL(import.meta.env.VITE_API_URL).host 
    : `${hostname}:8000`;
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${backendHost}/ws/department-management/`;
};

export default function Departments() {
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  
  // Dialog States
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [selectedDept, setSelectedDept] = useState<Department | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // Alert Status
  const [isDeleteAlertOpen, setIsDeleteAlertOpen] = useState(false);
  const [deptToDelete, setDeptToDelete] = useState<string | null>(null);

  const { lastMessage, readyState, sendMessage } = useWebSocket(getWsUrl());

  // Init Data Fetching
  useEffect(() => {
    if (readyState === WebSocket.OPEN) {
      sendMessage({ action: "list" });
    }
  }, [readyState, sendMessage]);

  // Handle WS Messages
  useEffect(() => {
    if (!lastMessage) return;

    const { status, action, event, data, message } = lastMessage;

    if (status === "error") {
      let description = message;
      try {
        const errorDetail = JSON.parse(message);
        if (typeof errorDetail === 'object') {
          description = Object.entries(errorDetail)
            .map(([field, msgs]) => `${field}: ${Array.isArray(msgs) ? msgs.join(', ') : msgs}`)
            .join(' | ');
        }
      } catch (e) {
        // No es JSON, usar el mensaje tal cual
      }
      toast.error("Error en la operación", { description });
      setIsSubmitting(false);
      return;
    }

    if (status === "success") {
      if (action === "list") {
        setDepartments(data);
        setLoading(false);
      } else if (action === "create" || action === "update") {
        toast.success(action === "create" ? "Departamento Creado" : "Departamento Actualizado");
        setIsFormOpen(false);
        setIsSubmitting(false);
      } else if (action === "delete") {
        toast.success("Departamento eliminado lógica correctamente");
        setIsDeleteAlertOpen(false);
      }
    }

    // Handle Real-Time Broadcasts
    if (event === "department_created") {
      setDepartments((prev) => {
        if (!prev.find((d) => d.id === data.id)) return [...prev, data];
        return prev;
      });
    } else if (event === "department_updated") {
      setDepartments((prev) => prev.map((d) => (d.id === data.id ? data : d)));
    } else if (event === "department_deleted") {
      setDepartments((prev) => prev.filter((d) => d.id !== data.id));
    }

  }, [lastMessage]);

  const filteredDepts = useMemo(() => {
    return departments.filter(dept => {
      const q = search.toLowerCase();
      return (
        dept.name.toLowerCase().includes(q) ||
        dept.description?.toLowerCase().includes(q)
      );
    });
  }, [departments, search]);

  const handleOpenCreate = () => {
    setSelectedDept(null);
    setIsFormOpen(true);
  };

  const handleOpenEdit = (dept: Department) => {
    setSelectedDept(dept);
    setIsFormOpen(true);
  };

  const handleOpenDelete = (deptId: string) => {
    setDeptToDelete(deptId);
    setIsDeleteAlertOpen(true);
  };

  const submitForm = (payload: any) => {
    setIsSubmitting(true);
    if (selectedDept) {
      sendMessage({ action: "update", data: payload });
    } else {
      sendMessage({ action: "create", data: payload });
    }
  };

  const confirmDelete = () => {
    if (deptToDelete) {
      sendMessage({ action: "delete", data: { id: deptToDelete } });
    }
  };

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">Gestión de Departamentos</h2>
        <div className="flex items-center space-x-2">
          <Button onClick={handleOpenCreate} className="bg-primary hover:bg-primary/90">
            <Building className="mr-2 h-4 w-4" /> Nuevo Departamento
          </Button>
        </div>
      </div>

      <div className="bg-white/50 backdrop-blur-xl border border-border/50 shadow-sm rounded-xl p-4 overflow-hidden dark:bg-slate-900/50">
        <div className="flex items-center py-4">
          <div className="relative w-72">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Filtrar por nombre o descripción..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-8 bg-background border-muted"
            />
          </div>
        </div>

        <div className="rounded-md border bg-card">
          <Table>
            <TableHeader>
              <TableRow className="bg-muted/50">
                <TableHead>Departamento</TableHead>
                <TableHead>Descripción</TableHead>
                <TableHead>Última Actualización</TableHead>
                <TableHead>Auditado Por</TableHead>
                <TableHead className="text-right">Acciones</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                Array.from({ length: 3 }).map((_, i) => (
                  <TableRow key={i}>
                    <TableCell><Skeleton className="h-6 w-[200px]" /></TableCell>
                    <TableCell><Skeleton className="h-6 w-[300px]" /></TableCell>
                    <TableCell><Skeleton className="h-6 w-[120px]" /></TableCell>
                    <TableCell><Skeleton className="h-6 w-[150px]" /></TableCell>
                    <TableCell><Skeleton className="h-6 w-[80px] ml-auto" /></TableCell>
                  </TableRow>
                ))
              ) : filteredDepts.length > 0 ? (
                filteredDepts.map((dept) => (
                  <TableRow key={dept.id} className="transition-colors hover:bg-muted/50">
                    <TableCell>
                      <div className="font-semibold text-lg">{dept.name}</div>
                      <div className="text-xs text-muted-foreground uppercase tracking-widest">ID: {dept.id.substring(0, 8)}</div>
                    </TableCell>
                    <TableCell className="max-w-md">
                      <p className="text-sm truncate">
                        {dept.description || <span className="text-muted-foreground italic">Sin descripción</span>}
                      </p>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm">
                        {dept.updated_at 
                          ? new Date(dept.updated_at).toLocaleString()
                          : new Date(dept.created_at).toLocaleString()}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center space-x-2">
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger>
                              <div className="text-sm border-b border-dotted cursor-help">
                                {dept.updated_by_info?.email || dept.created_by_info?.email || "N/A"}
                              </div>
                            </TooltipTrigger>
                            <TooltipContent>
                              <p>Creado el: {new Date(dept.created_at).toLocaleString()}</p>
                              {dept.updated_at && <p>Actualizado: {new Date(dept.updated_at).toLocaleString()}</p>}
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                      </div>
                    </TableCell>
                    <TableCell className="text-right space-x-2">
                      <Button variant="outline" size="icon" onClick={() => handleOpenEdit(dept)}>
                        <Edit className="h-4 w-4 text-blue-500" />
                      </Button>
                      <Button variant="outline" size="icon" onClick={() => handleOpenDelete(dept.id)} className="hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-950">
                        <Trash2 className="h-4 w-4 text-red-500" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={5} className="h-24 text-center text-muted-foreground font-medium">
                    No hay departamentos registrados. Empieza por crear uno nuevo.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
      </div>

      <Dialog open={isFormOpen} onOpenChange={setIsFormOpen}>
        <DialogContent className="sm:max-w-[450px]">
          <DialogHeader>
            <DialogTitle className="flex items-center">
              <Building className="mr-2 h-5 w-5 text-primary" />
              {selectedDept ? "Modificar Departamento" : "Añadir Nuevo Departamento"}
            </DialogTitle>
          </DialogHeader>
          <DepartmentForm 
            initialData={selectedDept} 
            onSubmit={submitForm} 
            isLoading={isSubmitting} 
          />
        </DialogContent>
      </Dialog>

      <AlertDialog open={isDeleteAlertOpen} onOpenChange={setIsDeleteAlertOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>¿Está seguro de eliminar este departamento?</AlertDialogTitle>
            <AlertDialogDescription>
              Esta acción aplicará un **soft delete**. El departamento no se verá en los listados activos, pero la información de auditoría se mantendrá para fines de trazabilidad histórica.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction onClick={confirmDelete} className="bg-red-600 hover:bg-red-700">
              Confirmar Eliminación
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
