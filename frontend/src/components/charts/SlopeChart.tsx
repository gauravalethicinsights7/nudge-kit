import ReactECharts from "echarts-for-react";
import { AXIS_LABEL_STYLE, CHART_COLORS, TOOLTIP_BASE } from "./theme";

// Two-point before/after comparison (spec §16: slope chart). Used for prior
// updates — one line per item, from its planned/before value to its
// observed/after value. Chosen over a bar chart because the direction and
// magnitude of the shift is the actual analytical question, not the raw
// values in isolation.
export function SlopeChart({
  data,
  leftLabel = "Before",
  rightLabel = "After",
  height = 260,
  valueFormatter,
}: {
  data: { name: string; before: number; after: number }[];
  leftLabel?: string;
  rightLabel?: string;
  height?: number;
  valueFormatter?: (v: number) => string;
}) {
  const fmt = valueFormatter ?? ((v: number) => v.toFixed(2));

  const series = data.map((d, i) => ({
    name: d.name,
    type: "line" as const,
    data: [d.before, d.after],
    symbolSize: 7,
    lineStyle: { width: 2, color: CHART_COLORS[i % CHART_COLORS.length] },
    itemStyle: { color: CHART_COLORS[i % CHART_COLORS.length] },
    label: {
      show: true,
      formatter: (p: { dataIndex: number; value: number }) => (p.dataIndex === 1 ? `${d.name} ${fmt(p.value)}` : ""),
      position: "right" as const,
      fontSize: 11,
      color: "#172033",
    },
  }));

  const option = {
    grid: { left: 60, right: 140, top: 16, bottom: 24 },
    tooltip: {
      ...TOOLTIP_BASE,
      trigger: "item" as const,
      formatter: (p: { seriesName: string; value: number; dataIndex: number }) =>
        `${p.seriesName}<br/>${p.dataIndex === 0 ? leftLabel : rightLabel}: ${fmt(p.value)}`,
    },
    xAxis: {
      type: "category" as const,
      data: [leftLabel, rightLabel],
      axisLabel: { ...AXIS_LABEL_STYLE, fontWeight: 600 },
      axisLine: { lineStyle: { color: "#E4E7EC" } },
      axisTick: { show: false },
      boundaryGap: false,
    },
    yAxis: {
      type: "value" as const,
      show: false,
    },
    series,
  };

  return <ReactECharts option={option} style={{ height }} />;
}
