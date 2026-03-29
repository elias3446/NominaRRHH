import { useForm, useFieldArray } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { 
  Form, FormControl, FormField, FormItem, FormLabel, FormMessage 
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Department } from "@/types/department";
import { Plus, Trash2 } from "lucide-react";

const departmentSchema = z.object({
  id: z.string().optional(),
  name: z.string().min(3, "El nombre debe tener al menos 3 caracteres").max(100),
  description: z.string().max(500).optional().or(z.literal('')),
  job_roles: z.array(z.object({
    name: z.string().min(3, "El nombre del cargo es requerido"),
    description: z.string().max(500).optional().or(z.literal(''))
  })).optional(),
});

interface DepartmentFormProps {
  initialData: Department | null;
  onSubmit: (data: any) => void;
  isLoading: boolean;
}

export function DepartmentForm({ initialData, onSubmit, isLoading }: DepartmentFormProps) {
  const form = useForm<z.infer<typeof departmentSchema>>({
    resolver: zodResolver(departmentSchema),
    defaultValues: {
      id: initialData?.id || "",
      name: initialData?.name || "",
      description: initialData?.description || "",
      job_roles: [],
    },
  });

  const { fields, append, remove } = useFieldArray({
    control: form.control,
    name: "job_roles"
  });

  // Limpiar error genérico para asegurar UX correcta
  const handleOnSubmit = (data: any) => {
    onSubmit(data);
  };

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(handleOnSubmit)} className="space-y-4">
        <FormField
          control={form.control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Nombre del Departamento</FormLabel>
              <FormControl>
                <Input placeholder="Ej: Recursos Humanos" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        
        <FormField
          control={form.control}
          name="description"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Descripción (Opcional)</FormLabel>
              <FormControl>
                <Textarea 
                  placeholder="Describe brevemente las responsabilidades del departamento..." 
                  className="resize-none"
                  {...field} 
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        
        {!initialData && (
          <div className="space-y-4 pt-4 border-t">
            <div className="flex justify-between items-center">
              <div>
                <h3 className="font-semibold text-sm">Cargos asociados</h3>
                <p className="text-xs text-muted-foreground">Agrega cargos a este departamento (opcional)</p>
              </div>
              <Button 
                type="button" 
                variant="outline" 
                size="sm" 
                onClick={() => append({ name: "", description: "" })}
              >
                <Plus className="w-4 h-4 mr-2" />
                Añadir / Crear Cargo
              </Button>
            </div>
            
            <div className="space-y-3 max-h-[300px] overflow-y-auto px-1">
              {fields.map((field, index) => (
                <div key={field.id} className="flex gap-3 items-end p-3 rounded-lg border bg-muted/40">
                  <div className="flex-1 space-y-3">
                    <FormField
                      control={form.control}
                      name={`job_roles.${index}.name`}
                      render={({ field }) => (
                        <FormItem className="space-y-1">
                          <FormLabel className="text-xs font-semibold">Nombre del Cargo *</FormLabel>
                          <FormControl>
                            <Input placeholder="Ej: Especialista" className="h-8 text-xs" {...field} />
                          </FormControl>
                          <FormMessage className="text-[10px]" />
                        </FormItem>
                      )}
                    />
                    <FormField
                      control={form.control}
                      name={`job_roles.${index}.description`}
                      render={({ field }) => (
                        <FormItem className="space-y-1">
                          <FormLabel className="text-xs">Descripción</FormLabel>
                          <FormControl>
                            <Input placeholder="Rol y responsabilidades..." className="h-8 text-xs" {...field} />
                          </FormControl>
                          <FormMessage className="text-[10px]" />
                        </FormItem>
                      )}
                    />
                  </div>
                  <Button 
                    type="button" 
                    variant="ghost" 
                    size="icon" 
                    className="h-8 w-8 text-destructive opacity-70 hover:opacity-100 hover:bg-destructive/10 mb-[6px]"
                    onClick={() => remove(index)}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              ))}
              {fields.length === 0 && (
                <div className="text-center py-4 text-xs text-muted-foreground border-2 border-dashed rounded-lg">
                  No hay cargos configurados. Pulsa en "Añadir / Crear Cargo" para empezar.
                </div>
              )}
            </div>
          </div>
        )}
        
        <div className="flex justify-end space-x-2 pt-4">
          <Button type="submit" disabled={isLoading} className="w-full">
            {isLoading ? "Guardando..." : initialData ? "Actualizar Departamento" : "Crear Departamento"}
          </Button>
        </div>
      </form>
    </Form>
  );
}
