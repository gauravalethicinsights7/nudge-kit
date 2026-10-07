import ReactECharts from "echarts-for-react";
import { AXIS_LABEL_STYLE, CHART_COLORS, GRID_BASE, TOOLTIP_BASE, categoryAxis, valueAxis } from "./theme";

// Composition/contribution chart (spec §15 "stacked bar: composition,
// contribution, channel mix, segment breakdown"). Data is long-form
// {category, series, value} rows, pivoted here into one ECharts series per
// distinct `series` value.
export function StackedBarChart({
  data,
  category,
  series,
  value,
  height = 260,
  horizontal = false,
  valueFormatter,
}: {
  data: Record<string, unknown>[];
  category: string;
  series: string;
  value: string;
  height?: number;
  horizontal?: boolean;
  valueFormatter?: (v: number) => string;
}) {
  // Same bottom-up category-axis convention as BarChart — reverse for
  // horizontal so the caller's natural order reads top-to-bottom.
  let categories = Array.from(new Set(data.map((d) => String(d[category]))));
  if (horizontal) categories = categories.reverse();
  const seriesNames = Array.from(new Set(data.map((d) => String(d[series]))));

  const lookup = new Map(data.map((d) => [`${d[category]}__${d[series]}`, Number(d[value])]));

  const chartSeries = seriesNames.map((name, i) => ({
    name,
    type: "bar" as const,
    stack: "total",
    barMaxWidth: 28,
    itemStyle: { color: CHART_COLORS[i % CHART_COLORS.length] },
    data: categories.map((c) => lookup.get(`${c}__${name}`) ?? 0),
  }));

  const option = {
    grid: { ...GRID_BASE, top: seriesNames.length > 1 ? 36 : 12 },
    legend: seriesNames.length > 1
      ? { top: 0, left: 0, itemWidth: 10, itemHeight: 10, textStyle: { ...AXIS_LABEL_STYLE, fontSize: 11.5 } }
      : undefined,
    tooltip: {
      ...TOOLTIP_BASE,
      trigger: "axis" as const,
      axisPointer: { type: "shadow" as const },
      valueFormatter: valueFormatter as ((v: unknown) => string) | undefined,
    },
    xAxis: horizontal ? valueAxis({ formatter: valueFormatter }) : categoryAxis(categories),
    yAxis: horizontal
      ? { ...categoryAxis(categories), axisLabel: { ...AXIS_LABEL_STYLE, width: 140, overflow: "truncate" as const } }
      : valueAxis({ formatter: valueFormatter }),
    series: chartSeries,
  };

  return <ReactECharts option={option} style={{ height }} />;
}
