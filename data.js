const SHEET_ID = '1bfJk8VUQPg-GrMkj2qiXoxcs0RxJPmIBN9ujmXFkXMQ';
const API_KEY = 'AIzaSyBSzdf9aK6jqDZJnX-6br6pBw2chqSwC-U';
const SHEET_NAME = 'Ответы на форму';
const RANGE = `'${SHEET_NAME}'!A:D`;
const HISTORY_CSV_PATH = 'history.csv';

const MONTH_NAMES = ['Січень', 'Лютий', 'Березень', 'Квітень', 'Травень', 'Червень', 'Липень', 'Серпень', 'Вересень', 'Жовтень', 'Листопад', 'Грудень'];

function formatCurrency(amount) {
  return amount.toLocaleString('uk-UA') + ' ₴';
}

function parseCSV(text) {
  const rows = [];
  let row = [];
  let field = '';
  let inQuotes = false;

  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (inQuotes) {
      if (c === '"') {
        if (text[i + 1] === '"') { field += '"'; i++; }
        else { inQuotes = false; }
      } else {
        field += c;
      }
    } else if (c === '"') {
      inQuotes = true;
    } else if (c === ',') {
      row.push(field);
      field = '';
    } else if (c === '\r') {
      // ignore, line break is handled on \n
    } else if (c === '\n') {
      row.push(field);
      rows.push(row);
      row = [];
      field = '';
    } else {
      field += c;
    }
  }
  if (field.length > 0 || row.length > 0) {
    row.push(field);
    rows.push(row);
  }
  return rows;
}

function rowsToRecords(rows) {
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

    records.push({
      timestamp: String(timestamp),
      date: dateStr,
      day, month, year,
      category,
      amount,
      comment: comment || ''
    });
  }
  return records;
}

async function fetchLiveRows() {
  const url = `https://sheets.googleapis.com/v4/spreadsheets/${SHEET_ID}/values/${encodeURIComponent(RANGE)}?key=${API_KEY}`;
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error('Помилка завантаження даних: ' + res.status);
  }
  const data = await res.json();
  return rowsToRecords(data.values || []);
}

async function fetchHistoryRows() {
  const res = await fetch(HISTORY_CSV_PATH);
  if (!res.ok) return [];
  const text = await res.text();
  return rowsToRecords(parseCSV(text));
}

function recordKey(r) {
  return [r.timestamp, r.category, r.amount, r.comment].join('|');
}

// Merges the static archive (history.csv, past closed years) with the live Google Sheet
// (current active year), deduplicating by the same composite key used in add-year-to-history.py
// so a year present in both sources (transition period) isn't shown twice.
async function fetchExpenseRows() {
  const [historyRecords, liveRecords] = await Promise.all([fetchHistoryRows(), fetchLiveRows()]);

  const merged = [...historyRecords];
  const seen = new Set(historyRecords.map(recordKey));
  for (const r of liveRecords) {
    const key = recordKey(r);
    if (!seen.has(key)) {
      merged.push(r);
      seen.add(key);
    }
  }
  return merged;
}
