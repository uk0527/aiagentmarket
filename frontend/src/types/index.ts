export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  profile_image?: string;
  created_at: string;
  last_login?: string;
}

export interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (credentials: LoginCredentials) => Promise<User>;
  signup: (userData: SignupData) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface SignupData {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
}

export interface CartItem {
  id: number;
  name: string;
  description: string;
  price: number;
  image: string;
}

export interface CartContextType {
  items: CartItem[];
  loading: boolean;
  error: string | null;
  addToCart: (agentId: number) => Promise<void>;
  removeFromCart: (agentId: number) => Promise<void>;
  checkout: () => Promise<void>;
  refreshCart: () => Promise<void>;
} 