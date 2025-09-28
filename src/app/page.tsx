"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart3, Clock, AlertTriangle } from "lucide-react";
import { useState, useEffect } from "react";
import { useFilters } from "@/contexts/filter-context";
import { DelayChart } from "@/components/delay-chart";

export default function Home() {
  // Get filter state from context
  const { selectedPeriod, selectedRoute, selectedDate } = useFilters();
  const [stats, setStats] = useState({
    totalDepartures: 1247,
    delayedPercentage: 23.4,
    cancelledPercentage: 2.1,
    periodLabel: "Siste 7 dager",
    delayedTrend: {
      value: 2.1,
      isPositive: true,
      label: "fra forrige 7-dagers periode"
    },
    cancelledTrend: {
      value: 0.3,
      isPositive: true,
      label: "fra forrige 7-dagers periode"
    }
  });

  // Fetch real data from API
  useEffect(() => {
    const fetchStats = async () => {
      try {
        const url = new URL('/api/delays', window.location.origin);
        url.searchParams.set('period', selectedPeriod);
        url.searchParams.set('route', selectedRoute);
        if (selectedDate) {
          // Use local date to avoid timezone issues
          const year = selectedDate.getFullYear();
          const month = String(selectedDate.getMonth() + 1).padStart(2, '0');
          const day = String(selectedDate.getDate()).padStart(2, '0');
          url.searchParams.set('date', `${year}-${month}-${day}`);
        }
        
        const response = await fetch(url.toString());
        const result = await response.json();
        
        if (result.stats) {
          const periodLabels = {
            "1d": "Siste 24 timer",
            "7d": "Siste 7 dager", 
            "30d": "Siste 30 dager",
            "90d": "Siste 90 dager"
          };
          
          // For now, we'll use mock trend data since we need historical comparison
          // In a real implementation, you'd fetch previous period data for comparison
          const mockTrends = {
            "1d": { delayedChange: 2.1, cancelledChange: 0.5, label: "fra forrige 24 timer" },
            "7d": { delayedChange: 1.8, cancelledChange: -0.2, label: "fra forrige 7-dagers periode" },
            "30d": { delayedChange: 3.2, cancelledChange: 0.8, label: "fra forrige 30-dagers periode" },
            "90d": { delayedChange: -1.1, cancelledChange: -0.5, label: "fra forrige 90-dagers periode" }
          };
          
          const trend = mockTrends[selectedPeriod as keyof typeof mockTrends] || mockTrends["7d"];
          
          // Calculate delay percentage using business intelligence definition
          // (delayed_classified + severely_delayed) / total_departures
          const businessIntelligenceDelayPercentage = result.stats.delayedClassified && result.stats.severelyDelayed 
            ? Math.round(((result.stats.delayedClassified + result.stats.severelyDelayed) / result.stats.totalDepartures) * 100 * 10) / 10
            : result.stats.delayPercentage; // Fallback to original calculation
          
          setStats({
            totalDepartures: result.stats.totalDepartures,
            delayedPercentage: businessIntelligenceDelayPercentage,
            cancelledPercentage: result.stats.cancelledPercentage || 0,
            periodLabel: periodLabels[selectedPeriod as keyof typeof periodLabels] || "Siste 7 dager",
            delayedTrend: {
              value: Math.abs(trend.delayedChange),
              isPositive: trend.delayedChange > 0,
              label: trend.label
            },
            cancelledTrend: {
              value: Math.abs(trend.cancelledChange),
              isPositive: trend.cancelledChange > 0,
              label: trend.label
            }
          });
        }
      } catch (error) {
        console.error('Failed to fetch stats:', error);
      }
    };

    fetchStats();
  }, [selectedPeriod, selectedRoute, selectedDate]);
  
  return (
    <main className="flex-1 p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold">L2 Linje Forsinkelsesanalyse</h1>
        <p className="text-muted-foreground mt-2">Analyse av forsinkelser på L2 linje</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        {/* Total Departures */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Totalt antall avganger</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalDepartures.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              {stats.periodLabel}
            </p>
          </CardContent>
        </Card>

        {/* Delayed Percentage - Updated with Business Intelligence Logic */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Andel forsinket</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.delayedPercentage}%</div>
            <p className="text-xs text-muted-foreground">
              <span className={stats.delayedTrend?.isPositive ? "text-red-600" : "text-green-600"}>
                {stats.delayedTrend?.isPositive ? "+" : "-"}{stats.delayedTrend?.value?.toFixed(1)}%
              </span> {stats.delayedTrend?.label}
            </p>
          </CardContent>
        </Card>

        {/* Cancellation Rate - New Card */}
        <Card className={stats.cancelledPercentage > 5 ? "border-red-200 bg-red-50" : ""}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Andel kansellert</CardTitle>
            <AlertTriangle className={`h-4 w-4 ${stats.cancelledPercentage > 5 ? "text-red-600" : "text-muted-foreground"}`} />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${stats.cancelledPercentage > 5 ? "text-red-600" : ""}`}>
              {stats.cancelledPercentage}%
            </div>
            <p className="text-xs text-muted-foreground">
              <span className={stats.cancelledTrend?.isPositive ? "text-red-600" : "text-green-600"}>
                {stats.cancelledTrend?.isPositive ? "+" : "-"}{stats.cancelledTrend?.value?.toFixed(1)}%
              </span> {stats.cancelledTrend?.label}
            </p>
            {stats.cancelledPercentage > 5 && (
              <p className="text-xs text-red-600 font-medium mt-1">
                ⚠️ Over 5% terskelverdi
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Chart Section */}
      <div className="w-full">
        <DelayChart />
      </div>
    </main>
  )
}