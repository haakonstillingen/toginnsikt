"use client";

import { Calendar, Home, Route, Settings, Info, Train, ChevronDown } from "lucide-react";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
} from "@/components/ui/sidebar";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Calendar as CalendarComponent } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Button } from "@/components/ui/button";
import { useFilters } from "@/contexts/filter-context";
import { format } from "date-fns";
import { nb } from "date-fns/locale";

// Menu items for our dashboard
const items = [
  {
    title: "Dashboard",
    url: "#",
    icon: Home,
  },
  {
    title: "Innstillinger",
    url: "#",
    icon: Settings,
  },
  {
    title: "Om",
    url: "#",
    icon: Info,
  },
];

export function AppSidebar() {
  const { selectedPeriod, selectedRoute, selectedDate, setSelectedPeriod, setSelectedRoute, setSelectedDate } = useFilters();

  return (
    <Sidebar>
      <SidebarHeader>
        <div className="flex items-center gap-2 px-4 py-2">
          <div className="w-8 h-8 bg-primary rounded-md flex items-center justify-center">
            <Train className="w-4 h-4 text-primary-foreground" />
          </div>
          <span className="font-semibold text-lg">Toginnsikt</span>
        </div>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Navigasjon</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {/* Dashboard */}
              <SidebarMenuItem>
                <SidebarMenuButton asChild>
                  <a href="#">
                    <Home className="w-4 h-4" />
                    <span>Dashboard</span>
                  </a>
                </SidebarMenuButton>
              </SidebarMenuItem>

                                  {/* Period Filter */}
                    <SidebarMenuItem>
                      <SidebarMenuButton>
                        <Calendar className="w-4 h-4" />
                        <span>Periode</span>
                      </SidebarMenuButton>
                      <SidebarMenuSub>
                        <SidebarMenuSubItem>
                          <Select value={selectedPeriod} onValueChange={setSelectedPeriod}>
                            <SelectTrigger className="w-full border-0 shadow-none bg-transparent">
                              <SelectValue placeholder="Velg periode" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="1d">Siste 24 timer</SelectItem>
                              <SelectItem value="7d">Siste 7 dager</SelectItem>
                              <SelectItem value="30d">Siste 30 dager</SelectItem>
                              <SelectItem value="90d">Siste 90 dager</SelectItem>
                              <SelectItem value="custom">Tilpasset periode</SelectItem>
                            </SelectContent>
                          </Select>
                        </SidebarMenuSubItem>
                        {selectedPeriod === "1d" && (
                          <SidebarMenuSubItem>
                            <Popover>
                              <PopoverTrigger asChild>
                                <Button variant="ghost" className="w-full justify-start text-left font-normal">
                                  <Calendar className="mr-2 h-4 w-4" />
                                  {selectedDate ? format(selectedDate, "dd.MM.yyyy", { locale: nb }) : "Velg dato"}
                                </Button>
                              </PopoverTrigger>
                              <PopoverContent className="w-auto p-0" align="start">
                                <CalendarComponent
                                  mode="single"
                                  selected={selectedDate}
                                  onSelect={setSelectedDate}
                                  initialFocus
                                  locale={nb}
                                />
                              </PopoverContent>
                            </Popover>
                          </SidebarMenuSubItem>
                        )}
                      </SidebarMenuSub>
                    </SidebarMenuItem>

              {/* Route Filter */}
              <SidebarMenuItem>
                <SidebarMenuButton>
                  <Route className="w-4 h-4" />
                  <span>Rute</span>
                </SidebarMenuButton>
                <SidebarMenuSub>
                  <SidebarMenuSubItem>
                    <Select value={selectedRoute} onValueChange={setSelectedRoute}>
                      <SelectTrigger className="w-full border-0 shadow-none bg-transparent">
                        <SelectValue placeholder="Velg rute" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">Alle ruter</SelectItem>
                        <SelectItem value="myrvoll-oslo">Myrvoll → Oslo S</SelectItem>
                        <SelectItem value="oslo-ski">Oslo S → Ski</SelectItem>
                      </SelectContent>
                    </Select>
                  </SidebarMenuSubItem>
                </SidebarMenuSub>
              </SidebarMenuItem>

              {/* Settings */}
              <SidebarMenuItem>
                <SidebarMenuButton asChild>
                  <a href="#">
                    <Settings className="w-4 h-4" />
                    <span>Innstillinger</span>
                  </a>
                </SidebarMenuButton>
              </SidebarMenuItem>

              {/* About */}
              <SidebarMenuItem>
                <SidebarMenuButton asChild>
                  <a href="#">
                    <Info className="w-4 h-4" />
                    <span>Om</span>
                  </a>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter>
        <div className="px-4 py-2 text-sm text-muted-foreground">
          Om
        </div>
      </SidebarFooter>
    </Sidebar>
  );
}
