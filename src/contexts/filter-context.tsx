"use client";

import { createContext, useContext, useState, ReactNode } from "react";

interface FilterContextType {
  selectedPeriod: string;
  selectedRoute: string;
  selectedDate: Date | undefined;
  setSelectedPeriod: (period: string) => void;
  setSelectedRoute: (route: string) => void;
  setSelectedDate: (date: Date | undefined) => void;
}

const FilterContext = createContext<FilterContextType | undefined>(undefined);

export function FilterProvider({ children }: { children: ReactNode }) {
  const [selectedPeriod, setSelectedPeriod] = useState("7d");
  const [selectedRoute, setSelectedRoute] = useState("myrvoll-oslo");
  const [selectedDate, setSelectedDate] = useState<Date | undefined>(undefined);

  return (
    <FilterContext.Provider
      value={{
        selectedPeriod,
        selectedRoute,
        selectedDate,
        setSelectedPeriod,
        setSelectedRoute,
        setSelectedDate,
      }}
    >
      {children}
    </FilterContext.Provider>
  );
}

export function useFilters() {
  const context = useContext(FilterContext);
  if (context === undefined) {
    throw new Error("useFilters must be used within a FilterProvider");
  }
  return context;
}
