import ReactECharts from "echarts-for-react";
import { AXIS_LABEL_STYLE, CHART_COLORS, GRID_BASE, TOOLTIP_BASE, categoryAxis, valueAxis } from "./theme";

export function BarChart({
  data,
  x,
  y,
  height = 240,
  horizontal = false,
  color = CHART_COLORS[0],
  valueFormatter,
  onBarClick,
}: {
  data: Record<string, unknown>[];
  x: string;
  y: string;
  height?: number;
  horizontal?: boolean;
  color?: string;
  valueFormatter?: (v: number) => string;
  onBarClick?: (category: string) => void;
}) {
  // ECharts renders category-axis index 0 at the bottom when it's the y
  // axis (standard cartesian convention) — reverse so the caller's natural
  // "first = most important" ranking order reads top-to-bottom instead.
  const ordered = horizontal ? [...data].reverse() : data;
  const categories = ordered.map((d) => String(d[x]));
  const values = ordered.map((d) => Number(d[y]));

  const option = {
    grid: GRID_BASE,
    tooltip: {
      ...TOOLTIP_BASE,
      trigger: "axis" as const,
      axisPointer: { type: "shadow" as const },
      formatter: (params: { name: string; value: number }[]) => {
        const p = params[0];
        return `${p.name}<br/>${valueFormatter ? valueFormatter(p.value) : p.value}`;
      },
    },
    xAxis: horizontal ? valueAxis({ formatter: valueFormatter }) : categoryAxis(categories),
    yAxis: horizontal
      ? { ...categoryAxis(categories), axisLabel: { ...AXIS_LABEL_STYLE, width: 140, overflow: "truncate" as const } }
      : valueAxis({ formatter: valueFormatter }),
    series: [
      {
        type: "bar" as const,
        data: values,
        itemStyle: { color, borderRadius: horizontal ? [0, 4, 4, 0] : [4, 4, 0, 0] },
        barMaxWidth: 28,
      },
    ],
  };

  return (
    <ReactECharts
      option={option}
      style={{ height }}
      onEvents={onBarClick ? { click: (p: { name: string }) => onBarClick(p.name) } : undefined}
    />
  );
}
