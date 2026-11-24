import { Routes, Route, Navigate } from "react-router-dom";

import Login from "./pages/Login";
import Register from "./pages/Register";
import CustomerDashboard from "./pages/CustomerDashboard";
import Cart from "./pages/Cart";
import Checkout from "./pages/Checkout";
import MyOrders from "./pages/MyOrders";
import Notifications from "./pages/Notifications";
import AdminDashboard from "./pages/AdminDashboard";
import ManageProducts from "./pages/ManageProducts"; 
import ManageInventory from "./pages/ManageInventory"; 
import ManageOrders from "./pages/ManageOrders"; 
import ManageCustomers from "./pages/ManageCustomers"; 
function ProtectedRoute({ children }) {
  const token = localStorage.getItem("access_token");

  return token ? children : <Navigate to="/login" replace />;
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />

      <Route path="/login" element={<Login />} />

      <Route path="/register" element={<Register />} />

      <Route
        path="/dashboard"element={
          <ProtectedRoute>
            <CustomerDashboard />
          </ProtectedRoute>
        }
      />

      <Route
        path="/cart"
        element={
          <ProtectedRoute>
            <Cart />
          </ProtectedRoute>
        }
      />
      <Route
          path="/orders"
          element={
          <ProtectedRoute>
           <MyOrders />
          </ProtectedRoute>
          }
      />
      <Route path="/checkout" element={<Checkout />} />
      <Route path="/notifications"
       element={<ProtectedRoute> <Notifications /> 
        </ProtectedRoute> } 
      />
      <Route path="/admin"
       element={<ProtectedRoute>
       <AdminDashboard />
       </ProtectedRoute>
        }
      />
      <Route
       path="/admin/products"
        element={
       <ProtectedRoute>
       <ManageProducts />
       </ProtectedRoute>
        }
      />
      <Route
       path="/admin/inventory"
        element={
       <ProtectedRoute>
       <ManageInventory />
       </ProtectedRoute>
        }
      />
      <Route
       path="/admin/orders"
        element={
       <ProtectedRoute>
       <ManageOrders />
       </ProtectedRoute>
        }
      />

      <Route
       path="/admin/customers"
        element={
       <ProtectedRoute>
       <ManageCustomers />
       </ProtectedRoute>
        }
      />
      
    </Routes>
  );
}

export default App;