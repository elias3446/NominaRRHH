import { useState, useEffect, useMemo } from "react";
import { User } from "@/types/user";
import { useWebSocket } from "@/hooks/useWebSocket";
import { useAuth } from "@/hooks/useAuth";
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
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { UserForm } from "@/components/user-management/UserForm";
import { Edit, Trash2, UserPlus, Search } from "lucide-react";
import { toast } from "sonner";

// Get dynamic WS URL for local network support
const getWsUrl = () => {
  const hostname = typeof window !== 'undefined' ? window.location.hostname : 'localhost';
  const backendHost = import.meta.env.VITE_API_URL 
    ? new URL(import.meta.env.VITE_API_URL).host 
    : `${hostname}:8000`;
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${backendHost}/ws/user-management/`;
};

export default function Users() {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  
  // Dialog States
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // Alert Status
  const [isDeleteAlertOpen, setIsDeleteAlertOpen] = useState(false);
  const [userToDelete, setUserToDelete] = useState<string | null>(null);

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
      toast.error("Error en la operación", { description: message });
      setIsSubmitting(false);
      return;
    }

    if (status === "success" && action === "list") {
      setUsers(data);
      setLoading(false);
    }
    else if (status === "success" && (action === "create" || action === "update")) {
      toast.success(action === "create" ? "Usuario Creado" : "Usuario Actualizado");
      setIsFormOpen(false);
      setIsSubmitting(false);
      // Fetch full list again to avoid miss-sync, or wait for event broadcast
      // We will rely on real-time event broadcast to update the row.
    }
    else if (status === "success" && action === "delete") {
      toast.success("Usuario deshabilitado correctamente");
      setIsDeleteAlertOpen(false);
    }

    // Handle Real-Time Broadcasts
    if (event === "user_created") {
      setUsers((prev) => {
        if (!prev.find((u) => u.id === data.id)) return [...prev, data];
        return prev;
      });
    } else if (event === "user_updated") {
      setUsers((prev) => prev.map((u) => (u.id === data.id ? data : u)));
    } else if (event === "user_deleted") {
      setUsers((prev) => prev.filter((u) => u.id !== data.id));
    }

  }, [lastMessage]);

  const filteredUsers = useMemo(() => {
    return users.filter(user => {
      // Regla de Oro: No ver superadmins ni a uno mismo en esta lista
      if (user.is_super_admin || user.id === currentUser?.id) return false;

      const q = search.toLowerCase();
      return (
        user.email.toLowerCase().includes(q) ||
        user.profile?.first_name?.toLowerCase().includes(q) ||
        user.profile?.last_name?.toLowerCase().includes(q)
      );
    });
  }, [users, search, currentUser]);

  const handleOpenCreate = () => {
    setSelectedUser(null);
    setIsFormOpen(true);
  };

  const handleOpenEdit = (user: User) => {
    setSelectedUser(user);
    setIsFormOpen(true);
  };

  const handleOpenDelete = (userId: string) => {
    setUserToDelete(userId);
    setIsDeleteAlertOpen(true);
  };

  const submitForm = (payload: any) => {
    setIsSubmitting(true);
    if (selectedUser) {
      sendMessage({ action: "update", data: payload });
    } else {
      sendMessage({ action: "create", data: payload });
    }
  };

  const confirmDelete = () => {
    if (userToDelete) {
      sendMessage({ action: "delete", data: { id: userToDelete } });
    }
  };

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">Gestión de Usuarios</h2>
        <div className="flex items-center space-x-2">
          <Button onClick={handleOpenCreate} className="bg-primary hover:bg-primary/90">
            <UserPlus className="mr-2 h-4 w-4" /> Nuevo Usuario
          </Button>
        </div>
      </div>

      <div className="bg-white/50 backdrop-blur-xl border border-border/50 shadow-sm rounded-xl p-4 overflow-hidden dark:bg-slate-900/50">
        <div className="flex items-center py-4">
          <div className="relative w-72">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Filtrar correos o nombres..."
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
                <TableHead>Usuario</TableHead>
                <TableHead>Perfil</TableHead>
                <TableHead>Rol</TableHead>
                <TableHead>Último Acceso</TableHead>
                <TableHead className="text-right">Acciones</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <TableRow key={i}>
                    <TableCell><Skeleton className="h-6 w-[200px]" /></TableCell>
                    <TableCell><Skeleton className="h-6 w-[150px]" /></TableCell>
                    <TableCell><Skeleton className="h-6 w-[80px]" /></TableCell>
                    <TableCell><Skeleton className="h-6 w-[100px]" /></TableCell>
                    <TableCell><Skeleton className="h-6 w-[80px] ml-auto" /></TableCell>
                  </TableRow>
                ))
              ) : filteredUsers.length > 0 ? (
                filteredUsers.map((user) => (
                  <TableRow key={user.id} className="transition-colors hover:bg-muted/50">
                    <TableCell>
                      <div className="font-medium">{user.email}</div>
                      <div className="text-xs text-muted-foreground">ID: {user.id.substring(0, 8)}...</div>
                    </TableCell>
                    <TableCell>
                      {user.profile?.first_name || user.profile?.last_name ? (
                        <div className="capitalize">{`${user.profile?.first_name || ''} ${user.profile?.last_name || ''}`}</div>
                      ) : (
                        <span className="text-muted-foreground italic">No definido</span>
                      )}
                      <div className="text-xs text-muted-foreground">{user.profile?.position || 'Sin cargo'}</div>
                    </TableCell>
                    <TableCell>
                      <Badge variant={user.role === 'service_role' ? 'destructive' : 'secondary'} className="capitalize">
                        {user.role}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {user.last_login 
                        ? new Date(user.last_login).toLocaleDateString()
                        : <span className="text-muted-foreground">Nunca</span>}
                    </TableCell>
                    <TableCell className="text-right space-x-2">
                      <Button variant="outline" size="icon" onClick={() => handleOpenEdit(user)}>
                        <Edit className="h-4 w-4 text-blue-500" />
                      </Button>
                      <Button variant="outline" size="icon" onClick={() => handleOpenDelete(user.id)} className="hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-950">
                        <Trash2 className="h-4 w-4 text-red-500" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={5} className="h-24 text-center text-muted-foreground">
                    No se encontraron usuarios.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
      </div>

      <Dialog open={isFormOpen} onOpenChange={setIsFormOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>{selectedUser ? "Editar Usuario" : "Crear Usuario"}</DialogTitle>
          </DialogHeader>
          <UserForm 
            initialData={selectedUser} 
            onSubmit={submitForm} 
            isLoading={isSubmitting} 
          />
        </DialogContent>
      </Dialog>

      <AlertDialog open={isDeleteAlertOpen} onOpenChange={setIsDeleteAlertOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>¿Dar de baja este usuario?</AlertDialogTitle>
            <AlertDialogDescription>
              Esta acción marcará al usuario como eliminado (Soft Delete). El usuario ya no podrá iniciar sesión y desaparecerá de las listas activas, pero sus datos permanecerán seguros en el sistema por trazabilidad.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction onClick={confirmDelete} className="bg-red-600 hover:bg-red-700 focus:ring-red-600">
              Confirmar Baja
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
