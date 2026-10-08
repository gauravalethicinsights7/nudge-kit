/** Money is stored as a float but is never meaningful below the unit — a
 *  forecast of "1,048,958.595 INR" implies a precision the model does not
 *  have. Round to whole units, and abbreviate so a headline number can be
 *  read at a glance rather than counted digit by digit.
 *
 *  Scale words are currency-aware: crore/lakh for INR, M/K elsewhere. The
 *  platform ships india and us packs, so hard-coding either would be wrong
 *  half the time.
 */
export function fmtMoney(value: number, currency?: string): string {
  const n = Math.round(value);
  const abs = Math.abs(n);

  if (currency === "INR") {
    if (abs >= 10_000_000) return `${(n / 10_000_000).toFixed(2)} cr`;
    if (abs >= 100_000) return `${(n / 100_000).toFixed(2)} L`;
    return n.toLocaleString("en-IN");
  }

  if (abs >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`;
  if (abs >= 10_000) return `${(n / 1_000).toFixed(1)}K`;
  return n.toLocaleString();
}

/** Full-precision money, for tables and detail views where the exact figure
 *  matters more than scannability. */
export function fmtMoneyExact(value: number, currency?: string): string {
  return Math.round(value).toLocaleString(currency === "INR" ? "en-IN" : undefined);
}

export function fmtNum(value: number, maxFractionDigits = 1): string {
  return value.toLocaleString(undefined, { maximumFractionDigits: maxFractionDigits });
}
