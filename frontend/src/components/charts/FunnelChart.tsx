import ReactECharts from "echarts-for-react";
import { CHART_COLORS, TOOLTIP_BASE } from "./theme";

// Sequential conversion stages (spec §15: "Funnel — for sequential
// conversion stages"). Used for the patient funnel: prevalent -> diagnosed
// -> treated -> controlled.
export function FunnelChart({
  data,
  height = 260,
  valueFormatter,
}: {
  data: { name: string; value: number }[];
  height?: number;
  valueFormatter?: (v: number) => string;
}) {
  const option = {
    tooltip: {
      ...TOOLTIP_BASE,
      trigger: "item" as const,
      formatter: (p: { name: string; value: number }) => `${p.name}<br/>${valueFormatter ? valueFormatter(p.value) : p.value}`,
    },
    series: [
      {
        type: "funnel" as const,
        sort: "none" as const,
        left: "6%",
        right: "6%",
        top: 8,
        bottom: 8,
        width: "88%",
        minSize: "40%",
        maxSize: "100%",
        gap: 3,
        label: {
          show: true,
          position: "inside" as const,
          formatter: (p: { name: string; value: number }) => `${p.name}\n${valueFormatter ? valueFormatter(p.value) : p.value}`,
          fontSize: 11.5,
          color: "#fff",
          fontWeight: 600,
          lineHeight: 15,
        },
        itemStyle: { borderColor: "#fff", borderWidth: 2 },
        data: data.map((d, i) => ({ ...d, itemStyle: { color: CHART_COLORS[i % CHART_COLORS.length] } })),
      },
    ],
  };

  return <ReactECharts option={option} style={{ height }} />;
}
