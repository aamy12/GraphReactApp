import { useState } from "react";
import { Link, useLocation } from "wouter";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { useIsMobile } from "@/hooks/use-mobile";
import { Menu, Home, History, LogOut, BarChart, Upload, Search, Sun, Moon } from "lucide-react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

interface LayoutProps {
  children: React.ReactNode;
  onLogout: () => void;
}

export default function Layout({ children, onLogout }: LayoutProps) {
  const [location] = useLocation();
  const isMobile = useIsMobile();
  const [open, setOpen] = useState(false);
  const [theme, setTheme] = useState(localStorage.getItem('theme') || 'light'); // Add theme state

  // Parse user data from localStorage
  const userString = localStorage.getItem('user');
  const user = userString && userString !== 'undefined' ? JSON.parse(userString) : null;

  const navigation = [
    {
      name: "Dashboard",
      href: "/dashboard",
      icon: Home,
      current: location === "/dashboard",
    },
    {
      name: "Query Knowledge",
      href: "/query",
      icon: Search,
      current: location === "/query",
    },
    {
      name: "Upload Documents",
      href: "/upload",
      icon: Upload,
      current: location === "/upload",
    },
    {
      name: "History",
      href: "/history",
      icon: History,
      current: location === "/history",
    },
    {
      name: "Settings",
      href: "/settings",
      icon: BarChart,
      current: location === "/settings",
    },
  ];

  const handleLogout = () => {
    if (window.confirm("Are you sure you want to log out?")) {
      onLogout();
    }
  };

  const NavLinks = () => (
    <>
      <div className="px-3 py-2">
        <div className="flex items-center mb-6">
          <div className="flex items-center gap-2 text-lg font-semibold">
            <BarChart className="h-6 w-6 text-primary" />
            <span>Knowledge Graph</span>
          </div>
        </div>
        <div className="space-y-1">
          {navigation.map((item) => (
            <Link
              key={item.name}
              href={item.href}
              onClick={() => setOpen(false)}
            >
              <Button
                variant={item.current ? "secondary" : "ghost"}
                className="w-full justify-start"
              >
                <item.icon className="mr-2 h-4 w-4" />
                {item.name}
              </Button>
            </Link>
          ))}
        </div>
      </div>
      <div className="mt-auto px-3 py-2">
        {user && (
          <div className="mb-2 px-2 py-1.5 rounded-md">
            <p className="text-sm font-medium">{user.username}</p>
            <p className="text-xs text-muted-foreground truncate">{user.email}</p>
          </div>
        )}
        <Button
          variant="ghost"
          className="w-full justify-start text-red-500 hover:text-red-500 hover:bg-red-50"
          onClick={handleLogout}
        >
          <LogOut className="mr-2 h-4 w-4" />
          Logout
        </Button>
      </div>
    </>
  );

  return (
    <div className={`flex h-screen overflow-hidden bg-${theme === 'dark' ? 'dark' : 'background'}`}> {/* Apply theme to background */}
      {/* Mobile sidebar */}
      {isMobile ? (
        <Sheet open={open} onOpenChange={setOpen}>
          <SheetTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="absolute left-4 top-4 z-50"
            >
              <Menu className="h-5 w-5" />
              <span className="sr-only">Toggle Menu</span>
            </Button>
          </SheetTrigger>
          <SheetContent side="left" className="w-64 p-0 flex flex-col">
            <ScrollArea className="flex-1">
              <NavLinks />
            </ScrollArea>
          </SheetContent>
        </Sheet>
      ) : (
        <aside className="hidden md:flex md:w-64 md:flex-col md:fixed md:inset-y-0 z-50">
          <div className={`flex flex-col h-full border-r bg-${theme === 'dark' ? 'dark' : 'sidebar'} text-${theme === 'dark' ? 'white' : 'sidebar-foreground'}`}> {/* Apply theme to sidebar */}
            <ScrollArea className="flex-1 flex flex-col justify-between py-4">
              <NavLinks />
            </ScrollArea>
          </div>
        </aside>
      )}

      {/* Main content */}
      <main className={`flex-1 overflow-auto ${isMobile ? 'pt-16' : 'md:pl-64'}`}>
        <div className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          <div className="flex h-14 items-center px-4 gap-4 justify-end">
            {user && (
              <div className="flex items-center gap-2 mr-auto">
                <Avatar className="h-8 w-8">
                  <AvatarImage src={`https://www.gravatar.com/avatar/${user.email}?d=identicon`} />
                  <AvatarFallback>{user.username.charAt(0).toUpperCase()}</AvatarFallback>
                </Avatar>
                <div className="hidden md:block">
                  <p className="text-sm font-medium">{user.username}</p>
                  <p className="text-xs text-muted-foreground">{user.email}</p>
                </div>
              </div>
            )}
            <Button
              variant="outline"
              size="icon"
              className="shrink-0"
              onClick={() => {
                const newTheme = theme === "dark" ? "light" : "dark";
                setTheme(newTheme);
                localStorage.setItem('theme', newTheme);
              }}
            >
              {theme === "dark" ? (
                <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
              ) : (
                <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
              )}
              <span className="sr-only">Toggle theme</span>
            </Button>
          </div>
        </div>
        {children}
      </main>
    </div>
  );
}