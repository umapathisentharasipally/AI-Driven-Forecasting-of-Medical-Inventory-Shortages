export async function downloadBlobResponse(response, filename) {
  if (!response.ok) {
    throw new Error("Download failed");
  }

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);

  const link = document.createElement("a");
  link.href = url;
  link.download = filename;

  document.body.appendChild(link);
  link.click();

  link.remove();

  window.URL.revokeObjectURL(url);
}

export function buildFileName(prefix, extension) {
  const date = new Date()
    .toISOString()
    .slice(0, 10);

  return `${prefix}_${date}.${extension}`;
}