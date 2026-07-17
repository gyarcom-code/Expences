const INFLATION_DATA_PATH = 'inflation-data.json';

async function fetchInflationData() {
  const res = await fetch(INFLATION_DATA_PATH);
  if (!res.ok) return null;
  return res.json();
}

function getLatestInflationKey(inflationData) {
  const keys = Object.keys(inflationData).sort();
  return keys[keys.length - 1];
}

// Переводит номінальну суму за конкретний рік/місяць у ціни останнього
// доступного місяця в inflation-data.json ("скільки б це коштувало сьогодні").
// Якщо даних по інфляції немає (файл не завантажився, або місяць новіший за
// останній запис) — повертає суму без змін.
function adjustForInflation(amount, year, month, inflationData) {
  if (!inflationData) return amount;

  const key = `${year}-${String(month).padStart(2, '0')}`;
  const entry = inflationData[key];
  if (!entry) return amount;

  const baseKey = getLatestInflationKey(inflationData);
  const baseIndex = inflationData[baseKey].cumulativeIndex;
  return amount * (baseIndex / entry.cumulativeIndex);
}
