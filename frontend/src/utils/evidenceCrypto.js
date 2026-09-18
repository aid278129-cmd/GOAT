/**
 * Client-Side Cryptographic and Formatting Utilities for Evidence Provenance.
 * Computes deterministic SHA-256 digests over uploaded File / Blob byte arrays.
 */

export async function computeFileSHA256(fileOrBlob) {
  try {
    const arrayBuffer = await fileOrBlob.arrayBuffer();
    const hashBuffer = await window.crypto.subtle.digest('SHA-256', arrayBuffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    return hashHex;
  } catch (error) {
    console.warn('Error computing SHA-256 digest:', error);
    return null;
  }
}

export function formatBytes(bytes, decimals = 1) {
  if (!+bytes) return '0 Bytes';
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
}

export function formatTimestamp(date = new Date()) {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toISOString().replace('T', ' ').substring(0, 19) + ' UTC';
}

export function truncateHash(hash, front = 8, back = 6) {
  if (!hash) return 'UNHASHED';
  if (hash.length <= front + back) return hash;
  return `${hash.substring(0, front)}...${hash.substring(hash.length - back)}`;
}
