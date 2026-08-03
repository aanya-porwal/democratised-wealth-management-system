"use client";

import { api } from "@/lib/api/client";
import type { PageOut, UserOut } from "@/types/api";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  Users,
  ShieldAlert,
  Activity,
  RefreshCw,
  Search,
  Database,
  Server,
  Loader2,
} from "lucide-react";
import { useEffect, useState } from "react";
import type { SystemHealth, SystemReady } from "@/types/api";

export default function AdminPage() {
  const [users, setUsers] = useState<PageOut<UserOut> | null>(null);
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [ready, setReady] = useState<SystemReady | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const [userData, healthData, readyData] = await Promise.all([
        api.listUsers(1, 100, searchInput || undefined),
        api.systemHealth(),
        api.systemReady(),
      ]);
      setUsers(userData);
      setHealth(healthData);
      setReady(readyData);
    } catch {
      setUsers(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [search]);

  const setRole = async (userId: string, role: string) => {
    try {
      await api.setUserRole(userId, role);
      await load();
    } catch {
      // role change requires admin; ignore error
    }
  };

  const deleteUser = async (userId: string) => {
    try {
      await api.deleteUser(userId);
      await load();
    } catch {
      // ignore
    }
  };

  const adminCount = users?.items.filter((u) => u.role === "admin").length ?? 0;
  const userCount = users?.items.filter((u) => u.role === "user").length ?? 0;
  const advisorCount =
    users?.items.filter((u) => u.role === "advisor").length ?? 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-2xl font-bold tracking-tight">Admin Panel</h2>
            <Badge variant="outline">
              <ShieldAlert className="mr-1 h-3 w-3" aria-hidden />
              Admin
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground">
            Manage users, roles, market data, background jobs, logs and system
            health.
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={load}>
          <RefreshCw className="mr-2 h-4 w-4" aria-hidden />
          Refresh
        </Button>
      </div>

      {/* System health */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex-row items-center justify-between space-y-0">
            <CardTitle className="text-sm font-medium">API Status</CardTitle>
            <Server className="h-4 w-4 text-emerald-500" aria-hidden />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold capitalize">
              {health?.status ?? "—"}
            </div>
            <p className="text-xs text-muted-foreground">
              v{health?.version} · {health?.environment}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex-row items-center justify-between space-y-0">
            <CardTitle className="text-sm font-medium">Database</CardTitle>
            <Database className="h-4 w-4 text-blue-500" aria-hidden />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold capitalize">
              {ready?.database ?? "—"}
            </div>
            <p className="text-xs text-muted-foreground">PostgreSQL readiness</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex-row items-center justify-between space-y-0">
            <CardTitle className="text-sm font-medium">Redis</CardTitle>
            <Activity className="h-4 w-4 text-violet-500" aria-hidden />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold capitalize">
              {ready?.redis ?? "—"}
            </div>
            <p className="text-xs text-muted-foreground">Cache availability</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex-row items-center justify-between space-y-0">
            <CardTitle className="text-sm font-medium">Total Users</CardTitle>
            <Users className="h-4 w-4 text-amber-500" aria-hidden />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{users?.pagination.total ?? 0}</div>
            <p className="text-xs text-muted-foreground">
              {adminCount} admin · {advisorCount} advisor · {userCount} user
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Users table */}
      <Card>
        <CardHeader className="flex-row items-center justify-between space-y-0">
          <div>
            <CardTitle>User Management</CardTitle>
            <CardDescription>Search, promote and manage accounts</CardDescription>
          </div>
          <form
            className="flex w-64 items-center gap-2"
            onSubmit={(e) => {
              e.preventDefault();
              setSearch(searchInput);
            }}
          >
            <Input
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Search by name or email…"
              aria-label="Search users"
              className="h-8"
            />
            <Button type="submit" variant="outline" size="icon" className="h-8 w-8">
              <Search className="h-3.5 w-3.5" aria-hidden />
            </Button>
          </form>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" aria-hidden />
            </div>
          ) : users ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>User</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {users.items.map((user) => (
                  <TableRow key={user.id}>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Avatar className="h-7 w-7">
                          <AvatarFallback className="text-[10px]">
                            {user.full_name
                              .split(" ")
                              .map((n) => n[0])
                              .join("")
                              .slice(0, 2)}
                          </AvatarFallback>
                        </Avatar>
                        <span className="font-medium">{user.full_name}</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {user.email}
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={
                          user.role === "admin"
                            ? "destructive"
                            : user.role === "advisor"
                            ? "secondary"
                            : "outline"
                        }
                      >
                        {user.role}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={user.is_active ? "default" : "outline"}
                      >
                        {user.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        {user.role !== "admin" ? (
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-7 text-xs"
                            onClick={() => setRole(user.id, "advisor")}
                          >
                            Make advisor
                          </Button>
                        ) : null}
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 text-xs text-destructive hover:text-destructive"
                          onClick={() => deleteUser(user.id)}
                        >
                          Delete
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="py-12 text-center text-sm text-muted-foreground">
              Admin access required to view users.
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
