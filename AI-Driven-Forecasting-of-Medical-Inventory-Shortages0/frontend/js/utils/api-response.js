export function normalizeList(response) {
  if (Array.isArray(response)) return response;

  if (Array.isArray(response?.data)) return response.data;

  if (Array.isArray(response?.items)) return response.items;

  if (Array.isArray(response?.data?.items)) return response.data.items;

  if (Array.isArray(response?.results)) return response.results;
  if (Array.isArray(response?.data?.data)) return response.data.data;

  return [];
}

export function normalizeObject(response) {
  if (!response) return {};

  if (response.data && !Array.isArray(response.data)) {
    return response.data;
  }

  return response;
}