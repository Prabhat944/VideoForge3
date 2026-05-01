import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "sonner";
import "@/App.css";
import { AuthProvider } from "@/lib/auth";
import ProtectedRoute from "@/components/ProtectedRoute";
import Landing from "@/pages/Landing";
import Auth from "@/pages/Auth";
import Dashboard from "@/pages/Dashboard";
import Wizard from "@/pages/Wizard";
import Trends from "@/pages/Trends";
import Analytics from "@/pages/Analytics";
import Pricing from "@/pages/Pricing";
import BillingSuccess from "@/pages/BillingSuccess";
import CalendarPage from "@/pages/Calendar";
import AgentMode from "@/pages/AgentMode";
import Templates from "@/pages/Templates";
import ABTest from "@/pages/ABTest";

function App() {
    return (
        <div className="App">
            <AuthProvider>
                <BrowserRouter>
                    <Toaster
                        theme="dark"
                        position="top-right"
                        toastOptions={{
                            style: {
                                background: "#121214",
                                border: "1px solid rgba(255,255,255,0.1)",
                                color: "#fff",
                                borderRadius: "6px",
                            },
                        }}
                    />
                    <Routes>
                        <Route path="/" element={<Landing />} />
                        <Route path="/login" element={<Auth mode="login" />} />
                        <Route path="/register" element={<Auth mode="register" />} />
                        <Route path="/pricing" element={<Pricing />} />
                        <Route path="/billing/success" element={<ProtectedRoute><BillingSuccess /></ProtectedRoute>} />
                        <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
                        <Route path="/wizard" element={<ProtectedRoute><Wizard /></ProtectedRoute>} />
                        <Route path="/wizard/:id" element={<ProtectedRoute><Wizard /></ProtectedRoute>} />
                        <Route path="/agent" element={<ProtectedRoute><AgentMode /></ProtectedRoute>} />
                        <Route path="/calendar" element={<ProtectedRoute><CalendarPage /></ProtectedRoute>} />
                        <Route path="/templates" element={<ProtectedRoute><Templates /></ProtectedRoute>} />
                        <Route path="/ab-test/:id" element={<ProtectedRoute><ABTest /></ProtectedRoute>} />
                        <Route path="/trends" element={<ProtectedRoute><Trends /></ProtectedRoute>} />
                        <Route path="/analytics" element={<ProtectedRoute><Analytics /></ProtectedRoute>} />
                        <Route path="*" element={<Navigate to="/" replace />} />
                    </Routes>
                </BrowserRouter>
            </AuthProvider>
        </div>
    );
}

export default App;
