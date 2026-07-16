// ============================================================
// НАСТРОЙКИ визуальной индикации превышения трат на графиках
// динамики по месяцам (monthly-trends.html, category-trends.html).
// Главный график на index.html эти настройки не использует.
//
// Как это работает: для каждого выбранного года считается среднее
// по тем месяцам, где есть данные (пустые месяцы в расчёт не берутся,
// поэтому для незавершённого года среднее не занижается). Если сумма
// за конкретный месяц выше среднего — точка на графике красится:
//   - в жёлтый, если превышение меньше overageRedThreshold
//   - в красный, если превышение больше или равно overageRedThreshold
//
// Превышение считается в процентах:
//   (сумма_за_месяц - среднее) / среднее * 100
//
// Чтобы поменять пороги — просто измените цифры ниже и обновите
// страницу в браузере, менять код не нужно.
// ============================================================
const CHART_SETTINGS = {
  // При превышении среднего больше чем на этот % — точка жёлтая.
  // 0 означает "красить в жёлтый уже при любом превышении среднего".
  overageYellowThreshold: 0,

  // При превышении среднего больше чем на этот % — точка красная
  // (красный приоритетнее жёлтого, если оба условия выполняются).
  overageRedThreshold: 20,
};

const OVERAGE_COLOR_YELLOW = '#f4c430';
const OVERAGE_COLOR_RED = '#e53935';

// Среднее по месяцам, где реально есть данные (сумма > 0).
function computeMonthlyAverage(monthlyTotals) {
  const withData = monthlyTotals.filter(v => v > 0);
  if (withData.length === 0) return 0;
  return withData.reduce((sum, v) => sum + v, 0) / withData.length;
}

// Цвет точки для конкретного месяца: обычный цвет линии, либо жёлтый/красный
// при превышении среднего согласно порогам из CHART_SETTINGS.
function getOveragePointColor(value, average, baseColor) {
  if (average <= 0 || value <= average) return baseColor;

  const overagePercent = ((value - average) / average) * 100;
  if (overagePercent >= CHART_SETTINGS.overageRedThreshold) return OVERAGE_COLOR_RED;
  if (overagePercent >= CHART_SETTINGS.overageYellowThreshold) return OVERAGE_COLOR_YELLOW;
  return baseColor;
}
