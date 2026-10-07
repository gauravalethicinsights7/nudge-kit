// Shared ECharts styling so every chart in the app feels native to the
// product (spec §18: subtle gridlines, low-contrast axis, restrained
// legend/tooltip, no default chart-library look) instead of ad-hoc
// per-chart option objects.

export const CHART_COLORS = [
  "#1b365d", // navy (primary)
  "#d4af37", // gold (secondary)
  "#10b981", // emerald
  "#3b82f6", // blue
  "#ef4444", // red
  "#14b8a6", // teal
  "#f59e0b", // amber
  "#5a7499", // slate
];

export const AXIS_LABEL_STYLE = {
  color: "#5a7499",
  fontFamily: "Inter, sans-serif",
  fontSize: 11,
};

export const AXIS_LINE_STYLE = { lineStyle: { color: "rgba(27,54,93,0.12)" } };
export const SPLIT_LINE_STYLE = { lineStyle: { color: "rgba(27,54,93,0.08)", type: "solid" as const } };

export const TOOLTIP_BASE = {
  backgroundColor: "#1b365d",
  borderWidth: 0,
  padding: [8, 12],
  textStyle: { color: "#fff", fontFamily: "Inter, sans-serif", fontSize: 12 },
  extraCssText: "box-shadow: 0 4px 12px rgba(13,26,46,0.18); border-radius: 8px;",
};

export const GRID_BASE = { left: 8, right: 16, top: 12, bottom: 8, containLabel: true };

export function categoryAxis(data: string[], horizontal = false) {
  return {
    type: "category" as const,
    data,
    axisLabel: AXIS_LABEL_STYLE,
    axisLine: AXIS_LINE_STYLE,
    axisTick: { show: false },
    splitLine: { show: false },
    ...(horizontal ? {} : {}),
  };
}

export function valueAxis(opts?: { name?: string; formatter?: (v: number) => string }) {
  return {
    type: "value" as const,
    name: opts?.name,
    nameTextStyle: { ...AXIS_LABEL_STYLE, padding: [0, 0, 4, 0] },
    axisLabel: { ...AXIS_LABEL_STYLE, formatter: opts?.formatter },
    axisLine: { show: false },
    axisTick: { show: false },
    splitLine: SPLIT_LINE_STYLE,
  };
}
