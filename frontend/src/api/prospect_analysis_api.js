/**
 * Analysis API — wraps POST /api/analysis/upload.
 *
 * The backend returns competitor dates as ISO strings ("YYYY-MM-DD").
 * _hydrateDates converts them back to JS Date objects so Dashboard.jsx
 * can call .toLocaleDateString() without any changes.
 */

import { prospectApiFetch } from "./prospect_api_client";

/**
 * Upload a Helium 10 Xray .xlsx and receive the full market analysis.
 *
 * @param {File}   file
 * @param {object} [opts]
 * @param {number} [opts.topN=10]
 * @param {number} [opts.usdRate=17]
 * @returns {Promise<object>}
 */
export async function uploadXlsxForAnalysis(file, { topN = 10, usdRate = 17 } = {}) {
  const form = new FormData();
  form.append("file", file);
  form.append("top_n", String(topN));
  form.append("usd_rate", String(usdRate));

  const response = await prospectApiFetch("/analysis/upload", {
    method: "POST",
    body: form,
  });

  return _hydrateDates(response.data);
}

function _hydrateDates(data) {
  if (!data) return data;
  return {
    ...data,
    competitors: (data.competitors || []).map((c) => ({
      ...c,
      date: c.date ? new Date(c.date) : null,
    })),
  };
}
