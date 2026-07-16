const SHEET_ID = '1bfJk8VUQPg-GrMkj2qiXoxcs0RxJPmIBN9ujmXFkXMQ';
const API_KEY = 'AIzaSyBSzdf9aK6jqDZJnX-6br6pBw2chqSwC-U';
const SHEET_NAME = 'Ответы на форму';
const RANGE = `'${SHEET_NAME}'!A:D`;

const MONTH_NAMES = ['Січень', 'Лютий', 'Березень', 'Квітень', 'Травень', 'Червень', 'Липень', 'Серпень', 'Вересень', 'Жовтень', 'Листопад', 'Грудень'];

function formatCurrency(amount) {
  return amount.toLocaleString('uk-UA') + ' ₴';
}

async function fetchExpenseRows() {
  const url = `https://sheets.googleapis.com/v4/spreadsheets/${SHEET_ID}/values/${encodeURIComponent(RANGE)}?key=${API_KEY}`;
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error('Помилка завантаження даних: ' + res.status);
  }
  const data = await res.json();
  const rows = data.values || [];

  const records = [];
  for (let i = 1; i < rows.length; i++) {
    const row = rows[i];
    if (!row || row.length < 3) continue;
    const [timestamp, category, amountRaw, comment] = row;
    if (!timestamp || !category) continue;

    const match = String(timestamp).match(/^(\d{2})\.(\d{2})\.(\d{4})/);
    if (!match) continue;
    const day = parseInt(match[1], 10);
    const month = parseInt(match[2], 10);
    const year = parseInt(match[3], 10);
    const dateStr = `${match[1]}.${match[2]}.${match[3]}`;

    const amount = parseFloat(String(amountRaw).replace(',', '.'));
    if (isNaN(amount)) continue;

    records.push({ date: dateStr, day, month, year, category, amount, comment: comment || '' });
  }
  return records;
}
