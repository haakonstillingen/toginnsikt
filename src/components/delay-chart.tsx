"use client";

import { Bar, BarChart, XAxis, YAxis, CartesianGrid } from "recharts";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import { useState, useEffect } from "react";
import { useFilters } from "@/contexts/filter-context";

interface DelayData {
  hour: string;
  totalDepartures: number;
  delayedDepartures: number;
  avgDelay: number;
  maxDelay: number;
  delayPercentage: number;
  // Service categorization data
  onTimeDepartures: number;
  delayedClassified: number;
  cancelledDepartures: number;
  severelyDelayed: number;
  unknownDepartures: number;
  // Calculated percentages
  onTimePercentage: number;
  cancelledPercentage: number;
  severelyDelayedPercentage: number;
}

const chartConfig = {
  onTimeDepartures: {
    label: "I Riktig Tid",
    color: "#22c55e", // Green
  },
  delayedClassified: {
    label: "Forsinket",
    color: "#f59e0b", // Amber
  },
  cancelledDepartures: {
    label: "Kansellert",
    color: "#000000", // Black
  },
  severelyDelayed: {
    label: "Alvorlig Forsinket",
    color: "#ef4444", // Light red
  },
  unknownDepartures: {
    label: "Ukjent Status",
    color: "#6b7280", // Gray
  },
} as const;

export function DelayChart() {
  const { selectedPeriod, selectedRoute, selectedDate } = useFilters();
  const [data, setData] = useState<DelayData[]>([]);
  const [actualTimeRange, setActualTimeRange] = useState<{first_departure: string, last_departure: string} | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const url = new URL('/api/delays', window.location.origin);
        url.searchParams.set('period', selectedPeriod);
        url.searchParams.set('route', selectedRoute);
        if (selectedDate) {
          const year = selectedDate.getFullYear();
          const month = String(selectedDate.getMonth() + 1).padStart(2, '0');
          const day = String(selectedDate.getDate()).padStart(2, '0');
          url.searchParams.set('date', `${year}-${month}-${day}`);
        }

        const response = await fetch(url.toString());
        const result = await response.json();
        setData(result.data || []);
        setActualTimeRange(result.actualTimeRange || null);
      } catch (error) {
        console.error('Failed to fetch delay data:', error);
        setData([]);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [selectedPeriod, selectedRoute, selectedDate]);

  if (loading) {
    return (
      <div className="h-80 flex items-center justify-center">
        <div className="text-muted-foreground">Laster data...</div>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="h-80 flex items-center justify-center">
        <div className="text-muted-foreground">Ingen data tilgjengelig</div>
      </div>
    );
  }

  // Sort data by hour and filter based on actual time range for 1d period
  const sortedData = [...data]
    .sort((a, b) => new Date(a.hour).getTime() - new Date(b.hour).getTime())
    .filter(item => {
      if (selectedPeriod === '1d') {
        // If we have actual time range data, use it to filter
        if (actualTimeRange) {
          const itemTime = new Date(item.hour);
          const firstDeparture = new Date(actualTimeRange.first_departure);
          const lastDeparture = new Date(actualTimeRange.last_departure);
          return itemTime >= firstDeparture && itemTime <= lastDeparture;
        }
        // Show all hours if no actual time range (let actual data determine range)
        return true;
      }
      return true; // For daily data (7d, 30d, 90d), don't filter by hour
    })
    .map(item => ({
      ...item,
      // Ensure all service categorization fields have valid numbers
      onTimeDepartures: item.onTimeDepartures || 0,
      delayedClassified: item.delayedClassified || 0,
      cancelledDepartures: item.cancelledDepartures || 0,
      severelyDelayed: item.severelyDelayed || 0,
      unknownDepartures: item.unknownDepartures || 0,
    }))
    .filter(item => item.totalDepartures > 0); // Only show hours with actual departures


  // Check if we have any valid data after processing
  if (sortedData.length === 0) {
    return (
      <div className="h-80 flex items-center justify-center">
        <div className="text-muted-foreground">Ingen gyldig data tilgjengelig for valgt periode</div>
      </div>
    );
  }

  return (
    <div className="w-full">
      <h3 className="text-lg font-semibold mb-4">
        {selectedPeriod === '1d' ? 'Tjenestekvalitet per time' : 'Tjenestekvalitet per dag'}
      </h3>
      <p className="text-sm text-muted-foreground mb-4">
        {sortedData.length > 0 ? (
          <>
            {selectedPeriod === '1d' ? (
              <>
                {actualTimeRange ? (
                  <>
                    Viser data fra {new Date(actualTimeRange.first_departure).toLocaleTimeString('no-NO', { hour: '2-digit', minute: '2-digit' })} til {new Date(actualTimeRange.last_departure).toLocaleTimeString('no-NO', { hour: '2-digit', minute: '2-digit' })} (norsk tid)
                    <span className="text-green-600 ml-2">
                      (Faktisk tidsperiode - {sortedData.length} timer med data)
                    </span>
                  </>
                ) : (
                  <>
                    Viser data fra {new Date(sortedData[0].hour).toLocaleTimeString('no-NO', { hour: '2-digit', minute: '2-digit' })} til {new Date(sortedData[sortedData.length - 1].hour).toLocaleTimeString('no-NO', { hour: '2-digit', minute: '2-digit' })} (norsk tid)
                    {sortedData.length < 16 && (
                      <span className="text-amber-600 ml-2">
                        (Begrenset data - kun {sortedData.length} timer tilgjengelig)
                      </span>
                    )}
                  </>
                )}
              </>
            ) : (
              <>
                Viser data fra {new Date(sortedData[0].hour).toLocaleDateString('no-NO', { day: '2-digit', month: '2-digit' })} til {new Date(sortedData[sortedData.length - 1].hour).toLocaleDateString('no-NO', { day: '2-digit', month: '2-digit' })} (norsk tid)
                <span className="text-amber-600 ml-2">
                  ({sortedData.length} dager tilgjengelig)
                </span>
              </>
            )}
          </>
        ) : (
          'Ingen data tilgjengelig'
        )}
      </p>
      {/* Simple chart test - basic Recharts implementation */}
      <div className="h-80 w-full">
        <ChartContainer config={chartConfig} className="h-full w-full">
          <BarChart data={sortedData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="hour" 
              tickFormatter={(value) => {
                const date = new Date(value);
                if (selectedPeriod === '1d') {
                  return date.toLocaleTimeString('no-NO', { 
                    hour: '2-digit',
                    minute: '2-digit'
                  });
                } else {
                  return date.toLocaleDateString('no-NO', { 
                    day: '2-digit',
                    month: '2-digit'
                  });
                }
              }}
            />
            <YAxis 
              orientation="left"
              tickFormatter={(value) => `${value}`}
              label={{ value: 'Antall avganger', angle: -90, position: 'insideLeft' }}
            />
            <ChartTooltip 
              content={
                <ChartTooltipContent 
                  labelFormatter={(value) => {
                    const date = new Date(value);
                    if (selectedPeriod === '1d') {
                      return date.toLocaleTimeString('no-NO', {
                        hour: '2-digit',
                        minute: '2-digit'
                      });
                    } else {
                      return date.toLocaleDateString('no-NO', {
                        day: '2-digit',
                        month: '2-digit'
                      });
                    }
                  }}
                  formatter={(value, name) => {
                    // Only show categories with non-zero values
                    if (value === 0 || value === undefined || value === null) {
                      return null;
                    }
                    return [
                      `${value} avganger`,
                      chartConfig[name as keyof typeof chartConfig]?.label || name
                    ];
                  }}
                />
              }
            />
            <Bar 
              dataKey="onTimeDepartures" 
              stackId="service"
              fill={chartConfig.onTimeDepartures.color}
              name="onTimeDepartures"
            />
            <Bar 
              dataKey="delayedClassified" 
              stackId="service"
              fill={chartConfig.delayedClassified.color}
              name="delayedClassified"
            />
            <Bar 
              dataKey="severelyDelayed" 
              stackId="service"
              fill={chartConfig.severelyDelayed.color}
              name="severelyDelayed"
            />
            <Bar 
              dataKey="cancelledDepartures"
              stackId="service"
              fill={chartConfig.cancelledDepartures.color}
              name="cancelledDepartures"
            />
            <Bar 
              dataKey="unknownDepartures"
              stackId="service"
              fill={chartConfig.unknownDepartures.color}
              name="unknownDepartures"
            />
          </BarChart>
        </ChartContainer>
      </div>
      
      {/* Legend */}
      <div className="mt-4 flex flex-wrap gap-4 justify-center">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded" style={{ backgroundColor: chartConfig.onTimeDepartures.color }}></div>
          <span className="text-sm">{chartConfig.onTimeDepartures.label}</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded" style={{ backgroundColor: chartConfig.delayedClassified.color }}></div>
          <span className="text-sm">{chartConfig.delayedClassified.label}</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded" style={{ backgroundColor: chartConfig.severelyDelayed.color }}></div>
          <span className="text-sm">{chartConfig.severelyDelayed.label}</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded" style={{ backgroundColor: chartConfig.cancelledDepartures.color }}></div>
          <span className="text-sm">{chartConfig.cancelledDepartures.label}</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded" style={{ backgroundColor: chartConfig.unknownDepartures.color }}></div>
          <span className="text-sm">{chartConfig.unknownDepartures.label}</span>
        </div>
      </div>
    </div>
  );
}
