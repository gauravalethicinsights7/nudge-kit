import ReactECharts from "echarts-for-react";
import { AXIS_LABEL_STYLE, TOOLTIP_BASE } from "./theme";

// Matrix comparison across two categorical dimensions (spec §15: "Heatmap —
// for matrix comparisons, intensity, patterns across two categorical
// dimensions"). Used for the message-map grid (driver x brand x claim
// strength) and channel-fit scores (segment x channel x fit score).
export function HeatmapChart({
  data,
  x,
  y,
  value,
  height = 260,
  colorScale = ["#eef2f8", "#1b365d"],
  cellLabel,
  valueMin = 0,
  valueMax = 1,
}: {
  data: Record<string, unknown>[];
  x: string;
  y: string;
  value: string;
  height?: number;
  colorScale?: [string, string];
  cellLabel?: (v: number) => string;
  valueMin?: number;
  valueMax?: number;
}) {
  const xCats = Array.from(new Set(data.map((d) => String(d[x]))));
  const yCats = Array.from(new Set(data.map((d) => String(d[y]))));

  const cells = data.map((d) => [
    xCats.indexOf(String(d[x])),
    yCats.indexOf(String(d[y])),
    Number(d[value]),
  ]);

  const option = {
    grid: { left: 8, right: 16, top: 12, bottom: 48, containLabel: true },
    tooltip: {
      ...TOOLTIP_BASE,
      position: "top" as const,
      formatter: (p: { value: [number, number, number] }) => {
        const [xi, yi, v] = p.value;
        return `${yCats[yi]} &times; ${xCats[xi]}<br/>${cellLabel ? cellLabel(v) : v}`;
      },
    },
    xAxis: {
      type: "category" as const,
      data: xCats,
      splitArea: { show: true },
      axisLabel: { ...AXIS_LABEL_STYLE, rotate: xCats.some((c) => c.length > 10) ? 28 : 0 },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    yAxis: {
      type: "category" as const,
      data: yCats,
      splitArea: { show: true },
      axisLabel: AXIS_LABEL_STYLE,
      axisLine: { show: false },
      axisTick: { show: false },
    },
    visualMap: {
      min: valueMin,
      max: valueMax,
      show: false,
      inRange: { color: colorScale },
    },
    series: [
      {
        type: "heatmap" as const,
        data: cells,
        label: {
          show: true,
          formatter: (p: { value: [number, number, number] }) => (cellLabel ? cellLabel(p.value[2]) : String(p.value[2])),
          color: "#172033",
          fontSize: 10.5,
        },
        itemStyle: { borderColor: "#fff", borderWidth: 2, borderRadius: 3 },
        emphasis: { itemStyle: { shadowBlur: 6, shadowColor: "rgba(16,24,40,0.2)" } },
      },
    ],
  };

  return <ReactECharts option={option} style={{ height }} />;
}
