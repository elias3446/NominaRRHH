export interface UserProfile {
  id?: number;
  first_name: string;
  last_name: string;
  avatar?: string;
  phone_number?: string;
  address?: string;
  birth_date?: string;
  hire_date?: string;
  position?: string;
  employee_number?: string;
  base_salary?: string;
  department?: string;
}

export interface User {
  id: string;
  email: string;
  role: string;
  created_at: string;
  updated_at?: string;
  last_login?: string;
  email_confirmed_at?: string;
  phone?: string;
  phone_confirmed_at?: string;
  is_super_admin?: boolean;
  banned_until?: string;
  is_sso_user?: boolean;
  profile?: UserProfile;
}
