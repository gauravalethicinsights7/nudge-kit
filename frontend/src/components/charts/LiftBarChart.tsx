import ReactECharts from "echarts-for-react";
import { AXIS_LABEL_STYLE, CHART_COLORS, GRID_BASE, TOOLTIP_BASE, valueAxis } from "./theme";

// Horizontal bar with confidence-interval whiskers — comparison of lift
// across tests, where the CI width communicates how much to trust each
// estimate (spec §1/§13: "what changed" needs a confidence signal, not just
// a bare number). A custom renderItem draws the whisker since ECharts has
// no first-class error-bar series.
export function LiftBarChart({
  data,
  height = 240,
}: {
  data: { name: string; effect: number; ci_low: number; ci_high: number }[];
  height?: number;
}) {
  const names = data.map((d) => d.name);

  const whiskerData = data.map((d, i) => [i, d.ci_low, d.ci_high]);

  const option = {
    grid: { ...GRID_BASE, left: 16 },
    tooltip: {
      ...TOOLTIP_BASE,
      trigger: "item" as const,
      formatter: (p: { dataIndex: number }) => {
        const d = data[p.dataIndex];
        return `${d.name}<br/>Effect: ${d.effect.toFixed(2)}<br/>95% CI: ${d.ci_low.toFixed(2)} &ndash; ${d.ci_high.toFixed(2)}`;
      },
    },
    xAxis: valueAxis(),
    yAxis: {
      type: "category" as const,
      data: names,
      axisLabel: { ...AXIS_LABEL_STYLE, width: 140, overflow: "truncate" as const },
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { show: false },
    },
    series: [
      {
        type: "bar" as const,
        data: data.map((d) => d.effect),
        barMaxWidth: 16,
        itemStyle: { color: CHART_COLORS[0], borderRadius: [0, 3, 3, 0] },
        z: 2,
      },
      {
        type: "custom" as const,
        renderItem: (
          _params: unknown,
          api: {
            coord: (v: [number, number]) => [number, number];
            value: (i: number) => number;
            style: () => Record<string, unknown>;
          },
        ) => {
          const idx = api.value(0);
          const lowPt = api.coord([api.value(1), idx]);
          const highPt = api.coord([api.value(2), idx]);
          const capHeight = 6;
          const style = api.style();
          return {
            type: "group",
            children: [
              { type: "line", shape: { x1: lowPt[0], y1: lowPt[1], x2: highPt[0], y2: highPt[1] }, style: { ...style, fill: null, stroke: "#172033", lineWidth: 1.5 } },
              { type: "line", shape: { x1: lowPt[0], y1: lowPt[1] - capHeight / 2, x2: lowPt[0], y2: lowPt[1] + capHeight / 2 }, style: { ...style, fill: null, stroke: "#172033", lineWidth: 1.5 } },
              { type: "line", shape: { x1: highPt[0], y1: highPt[1] - capHeight / 2, x2: highPt[0], y2: highPt[1] + capHeight / 2 }, style: { ...style, fill: null, stroke: "#172033", lineWidth: 1.5 } },
            ],
          };
        },
        encode: { x: [1, 2], y: 0 },
        data: whiskerData,
        z: 3,
      },
    ],
  };

  return <ReactECharts option={option} style={{ height }} />;
}
