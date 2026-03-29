import { User } from "./user";

export interface Department {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at?: string;
  created_by?: string;
  updated_by?: string;
  created_by_info?: User;
  updated_by_info?: User;
}
