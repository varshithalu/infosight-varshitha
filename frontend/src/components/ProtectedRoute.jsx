import React from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const ProtectedRoute = ({ children }) => {
  const { token } = useAuth();

  if (!token) {
    // User not authenticated, redirect to login page
    return <Navigate to="/" />;
  }

  return children;
};

export default ProtectedRoute;
