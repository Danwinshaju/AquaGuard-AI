const DATABASE_NAME = "aquaguard-user-media";
const DATABASE_VERSION = 1;
const EVIDENCE_STORE = "incident-evidence";
const VIDEO_STORE = "processed-videos";
const RETENTION_MS = 24 * 60 * 60 * 1000;

interface StoredEvidence {
  key: string;
  ownerId: string;
  incidentId: string;
  snapshot: Blob;
  clip: Blob;
  createdAt: string;
}

interface StoredProcessedVideo {
  key: string;
  ownerId: string;
  videoId: string;
  video: Blob;
  createdAt: string;
}

export interface LocalEvidenceUrls {
  snapshotUrl: string;
  clipUrl: string;
}

function openDatabase(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    if (!window.indexedDB) {
      reject(new Error("This browser does not support private device storage."));
      return;
    }
    const request = window.indexedDB.open(DATABASE_NAME, DATABASE_VERSION);
    request.onupgradeneeded = () => {
      const database = request.result;
      if (!database.objectStoreNames.contains(EVIDENCE_STORE)) {
        database.createObjectStore(EVIDENCE_STORE, { keyPath: "key" });
      }
      if (!database.objectStoreNames.contains(VIDEO_STORE)) {
        database.createObjectStore(VIDEO_STORE, { keyPath: "key" });
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error ?? new Error("Device storage could not open."));
  });
}

async function getRecord<T>(storeName: string, key: string): Promise<T | undefined> {
  const database = await openDatabase();
  try {
    return await new Promise<T | undefined>((resolve, reject) => {
      const request = database.transaction(storeName, "readonly").objectStore(storeName).get(key);
      request.onsuccess = () => resolve(request.result as T | undefined);
      request.onerror = () => reject(request.error);
    });
  } finally {
    database.close();
  }
}

async function putRecord(storeName: string, value: StoredEvidence | StoredProcessedVideo) {
  const database = await openDatabase();
  try {
    await new Promise<void>((resolve, reject) => {
      const transaction = database.transaction(storeName, "readwrite");
      transaction.objectStore(storeName).put(value);
      transaction.oncomplete = () => resolve();
      transaction.onerror = () => reject(transaction.error);
      transaction.onabort = () => reject(transaction.error);
    });
  } finally {
    database.close();
  }
}

async function deleteRecord(storeName: string, key: string) {
  const database = await openDatabase();
  try {
    await new Promise<void>((resolve, reject) => {
      const transaction = database.transaction(storeName, "readwrite");
      transaction.objectStore(storeName).delete(key);
      transaction.oncomplete = () => resolve();
      transaction.onerror = () => reject(transaction.error);
    });
  } finally {
    database.close();
  }
}

async function fetchBlob(url: string, expectedType: "image" | "video"): Promise<Blob> {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Evidence is unavailable (${response.status}).`);
  const blob = await response.blob();
  if (!blob.size || (blob.type && !blob.type.startsWith(`${expectedType}/`))) {
    throw new Error(`The ${expectedType} evidence returned by the server is invalid.`);
  }
  return blob;
}

export async function moveIncidentEvidenceToDevice(
  ownerId: string,
  incident: { id: string; snapshot_url: string; clip_url: string; created_at: string },
): Promise<LocalEvidenceUrls> {
  const key = `${ownerId}:${incident.id}`;
  let stored = await getRecord<StoredEvidence>(EVIDENCE_STORE, key);
  if (!stored) {
    const [snapshot, clip] = await Promise.all([
      fetchBlob(incident.snapshot_url, "image"),
      fetchBlob(incident.clip_url, "video"),
    ]);
    stored = {
      key,
      ownerId,
      incidentId: incident.id,
      snapshot,
      clip,
      createdAt: incident.created_at,
    };
    await putRecord(EVIDENCE_STORE, stored);
  }

  // Server deletion happens only after both blobs have committed to IndexedDB.
  const release = await fetch(`/api/v1/incidents/${incident.id}/release-evidence`, {
    method: "POST",
  });
  if (!release.ok && release.status !== 404) {
    throw new Error(`Server evidence could not be released (${release.status}).`);
  }
  return {
    snapshotUrl: URL.createObjectURL(stored.snapshot),
    clipUrl: URL.createObjectURL(stored.clip),
  };
}

export async function moveProcessedVideoToDevice(
  ownerId: string,
  videoId: string,
  downloadUrl: string,
): Promise<string> {
  const key = `${ownerId}:${videoId}`;
  let stored = await getRecord<StoredProcessedVideo>(VIDEO_STORE, key);
  if (!stored) {
    const video = await fetchBlob(downloadUrl, "video");
    stored = { key, ownerId, videoId, video, createdAt: new Date().toISOString() };
    await putRecord(VIDEO_STORE, stored);
  }
  const release = await fetch(`/api/v1/videos/${videoId}/release`, { method: "POST" });
  if (!release.ok && release.status !== 404) {
    throw new Error(`Temporary server video could not be released (${release.status}).`);
  }
  return URL.createObjectURL(stored.video);
}

export function deleteIncidentEvidence(ownerId: string, incidentId: string): Promise<void> {
  return deleteRecord(EVIDENCE_STORE, `${ownerId}:${incidentId}`);
}

async function deleteOwnerRecords(storeName: string, ownerId: string, expiredOnly: boolean) {
  const database = await openDatabase();
  try {
    await new Promise<void>((resolve, reject) => {
      const transaction = database.transaction(storeName, "readwrite");
      const request = transaction.objectStore(storeName).openCursor();
      request.onsuccess = () => {
        const cursor = request.result;
        if (!cursor) return;
        const record = cursor.value as StoredEvidence | StoredProcessedVideo;
        const expired = Date.now() - new Date(record.createdAt).getTime() >= RETENTION_MS;
        if (record.ownerId === ownerId && (!expiredOnly || expired)) cursor.delete();
        cursor.continue();
      };
      request.onerror = () => reject(request.error);
      transaction.oncomplete = () => resolve();
      transaction.onerror = () => reject(transaction.error);
    });
  } finally {
    database.close();
  }
}

export async function clearOwnerIncidentEvidence(ownerId: string): Promise<void> {
  await deleteOwnerRecords(EVIDENCE_STORE, ownerId, false);
}

export async function purgeExpiredOwnerMedia(ownerId: string): Promise<void> {
  await Promise.all([
    deleteOwnerRecords(EVIDENCE_STORE, ownerId, true),
    deleteOwnerRecords(VIDEO_STORE, ownerId, true),
  ]);
}

export async function requestPersistentDeviceStorage(): Promise<boolean> {
  return navigator.storage?.persist ? navigator.storage.persist() : false;
}
