import React, { createContext, useState, useContext } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(localStorage.getItem("token"));
  const navigate = useNavigate();

  const login = async (email, password) => {
    try {
      const response = await api.post("/auth/login", { email, password });
      const { access_token } = response.data;
      localStorage.setItem("token", access_token);
      setToken(access_token);
      navigate("/chat");
    } catch (error) {
      console.error("Login failed:", error);
      alert("Login failed! Please check your credentials.");
    }
  };

  const signup = async (
    firstName,
    lastName,
    email,
    password,
    confirmPassword
  ) => {
    if (password !== confirmPassword) {
      alert("Passwords do not match!");
      return;
    }
    try {
      await api.post("/auth/signup", {
        first_name: firstName,
        last_name: lastName,
        email,
        password,
        confirm_password: confirmPassword,
      });
      // After successful signup, redirect to login
      navigate("/");
      alert("Signup successful! Please log in.");
    } catch (error) {
      console.error("Signup failed:", error);
      alert("Signup failed! The email might already be registered.");
    }
  };

  const logout = () => {
    localStorage.removeItem("token");
    setToken(null);
    navigate("/");
  };

  const value = {
    token,
    login,
    signup,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// Custom hook to use the auth context easily in other components
export const useAuth = () => {
  return useContext(AuthContext);
};
