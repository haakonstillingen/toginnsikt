"use client";

import * as React from "react";
import {
  ColumnDef,
  ColumnFiltersState,
  SortingState,
  VisibilityState,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { ArrowUpDown, ChevronDown } from "lucide-react";
import { format, parse } from "date-fns";
import { nb } from "date-fns/locale";

import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useFilters } from "@/contexts/filter-context";
import { Skeleton } from "@/components/ui/skeleton";

// Type definition matching API response
export type Departure = {
  lineCode: string;
  plannedTime: string;
  actualTime: string | null;
  delayMinutes: number;
  isCancelled: boolean;
};

// Column definitions
export const columns: ColumnDef<Departure>[] = [
  {
    accessorKey: "lineCode",
    header: "Linje",
    cell: ({ row }) => (
      <div className="font-medium">{row.getValue("lineCode")}</div>
    ),
  },
  {
    accessorKey: "plannedTime",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          className="h-8 px-2"
        >
          Planlagt avgang
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      );
    },
    cell: ({ row }) => {
      const plannedTime = row.getValue("plannedTime") as string;
      try {
        // Parse the time string (format: "YYYY-MM-DD HH24:MI:SS")
        const date = parse(plannedTime, "yyyy-MM-dd HH:mm:ss", new Date());
        return (
          <div className="font-mono">
            {format(date, "HH:mm", { locale: nb })}
          </div>
        );
      } catch {
        return <div className="text-muted-foreground">-</div>;
      }
    },
  },
  {
    accessorKey: "actualTime",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          className="h-8 px-2"
        >
          Faktisk avgang
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      );
    },
    cell: ({ row }) => {
      const actualTime = row.getValue("actualTime") as string | null;
      if (!actualTime) {
        return <div className="text-muted-foreground">N/A</div>;
      }
      try {
        const date = parse(actualTime, "yyyy-MM-dd HH:mm:ss", new Date());
        return (
          <div className="font-mono">
            {format(date, "HH:mm", { locale: nb })}
          </div>
        );
      } catch {
        return <div className="text-muted-foreground">N/A</div>;
      }
    },
  },
  {
    accessorKey: "delayMinutes",
    header: ({ column }) => {
      return (
        <div className="text-right">
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
            className="h-8 px-2"
          >
            Forsinkelse (min)
            <ArrowUpDown className="ml-2 h-4 w-4" />
          </Button>
        </div>
      );
    },
    cell: ({ row }) => {
      const delay = row.getValue("delayMinutes") as number;
      return (
        <div className="text-right font-medium">
          {delay > 0 ? (
            <span className="text-orange-600">{delay}</span>
          ) : (
            <span className="text-green-600">0</span>
          )}
        </div>
      );
    },
  },
  {
    accessorKey: "isCancelled",
    header: "Kansellert",
    cell: ({ row }) => {
      const isCancelled = row.getValue("isCancelled") as boolean;
      return (
        <div className={isCancelled ? "text-red-600 font-medium" : ""}>
          {isCancelled ? "Ja" : "Nei"}
        </div>
      );
    },
  },
];

export function DeparturesTable() {
  const { selectedPeriod, selectedRoute, selectedDate } = useFilters();
  const [data, setData] = React.useState<Departure[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  const [sorting, setSorting] = React.useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>(
    []
  );
  const [columnVisibility, setColumnVisibility] =
    React.useState<VisibilityState>({});
  const [rowSelection, setRowSelection] = React.useState({});

  // Fetch data from API
  React.useEffect(() => {
    const fetchData = async () => {
      // Only fetch when period is 1d (24 hours)
      if (selectedPeriod !== "1d") {
        setData([]);
        setLoading(false);
        return;
      }

      setLoading(true);
      setError(null);

      try {
        const url = new URL("/api/departures", window.location.origin);
        url.searchParams.set("period", selectedPeriod);
        url.searchParams.set("route", selectedRoute);
        if (selectedDate) {
          const year = selectedDate.getFullYear();
          const month = String(selectedDate.getMonth() + 1).padStart(2, "0");
          const day = String(selectedDate.getDate()).padStart(2, "0");
          url.searchParams.set("date", `${year}-${month}-${day}`);
        }

        const response = await fetch(url.toString());
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        setData(result.departures || []);
      } catch (err) {
        console.error("Failed to fetch departures:", err);
        setError(
          err instanceof Error ? err.message : "Kunne ikke hente data"
        );
        setData([]);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [selectedPeriod, selectedRoute, selectedDate]);

  const table = useReactTable({
    data,
    columns,
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    onColumnVisibilityChange: setColumnVisibility,
    onRowSelectionChange: setRowSelection,
    state: {
      sorting,
      columnFilters,
      columnVisibility,
      rowSelection,
    },
    initialState: {
      pagination: {
        pageSize: 20,
      },
    },
  });

  // Don't render if period is not 1d
  if (selectedPeriod !== "1d") {
    return null;
  }

  // Loading state
  if (loading) {
    return (
      <div className="w-full">
        <div className="mb-4">
          <h3 className="text-lg font-semibold">
            Detaljert oversikt - Alle avganger
          </h3>
        </div>
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>
                  <Skeleton className="h-4 w-16" />
                </TableHead>
                <TableHead>
                  <Skeleton className="h-4 w-32" />
                </TableHead>
                <TableHead>
                  <Skeleton className="h-4 w-32" />
                </TableHead>
                <TableHead>
                  <Skeleton className="h-4 w-24" />
                </TableHead>
                <TableHead>
                  <Skeleton className="h-4 w-20" />
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {Array.from({ length: 5 }).map((_, i) => (
                <TableRow key={i}>
                  <TableCell>
                    <Skeleton className="h-4 w-8" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-4 w-16" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-4 w-16" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-4 w-12" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-4 w-12" />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="w-full">
        <div className="mb-4">
          <h3 className="text-lg font-semibold">
            Detaljert oversikt - Alle avganger
          </h3>
        </div>
        <div className="rounded-md border p-8 text-center">
          <p className="text-destructive">Feil ved henting av data</p>
          <p className="text-sm text-muted-foreground mt-2">{error}</p>
        </div>
      </div>
    );
  }

  // Empty state
  if (data.length === 0) {
    return (
      <div className="w-full">
        <div className="mb-4">
          <h3 className="text-lg font-semibold">
            Detaljert oversikt - Alle avganger
          </h3>
        </div>
        <div className="rounded-md border p-8 text-center">
          <p className="text-muted-foreground">
            Ingen data tilgjengelig for valgt periode
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full">
      <div className="mb-4">
        <h3 className="text-lg font-semibold">
          Detaljert oversikt - Alle avganger
        </h3>
        <p className="text-sm text-muted-foreground mt-1">
          Viser alle avganger for valgt rute og periode
        </p>
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => {
                  return (
                    <TableHead key={header.id}>
                      {header.isPlaceholder
                        ? null
                        : flexRender(
                            header.column.columnDef.header,
                            header.getContext()
                          )}
                    </TableHead>
                  );
                })}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows?.length ? (
              table.getRowModel().rows.map((row) => (
                <TableRow
                  key={row.id}
                  data-state={row.getIsSelected() && "selected"}
                >
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id}>
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext()
                      )}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell
                  colSpan={columns.length}
                  className="h-24 text-center"
                >
                  Ingen resultater.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-end space-x-2 py-4">
        <div className="flex-1 text-sm text-muted-foreground">
          {table.getFilteredRowModel().rows.length} avgang(er) totalt
        </div>
        <div className="space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
          >
            Forrige
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
          >
            Neste
          </Button>
        </div>
      </div>
    </div>
  );
}
