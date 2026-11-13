import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
});

export const api = {
  // Health
  getHealth: async () => {
    const res = await client.get('/api/health');
    return res.data;
  },

  // Hash Lab
  compareHashes: async (message: string, algorithms: string[]) => {
    const res = await client.post('/api/hash/compare', { message, algorithms });
    return res.data;
  },

  // Collision
  verifyCollision: async (input1_hex?: string, input2_hex?: string) => {
    const res = await client.post('/api/collision/verify', {
      input1_hex: input1_hex || null,
      input2_hex: input2_hex || null,
    });
    return res.data;
  },

  // EV Simulator
  getStations: async () => {
    const res = await client.get('/api/simulator/stations');
    return res.data;
  },

  generateEVMessage: async (station_id: string, message_type: string) => {
    const res = await client.post('/api/ev/messages', { station_id, message_type });
    return res.data;
  },

  // Legacy MD5
  legacyVerify: async (payload_json: string, legacy_md5: string) => {
    const res = await client.post('/api/legacy/verify', { payload_json, legacy_md5 });
    return res.data;
  },

  // SHA-3 Migration Wrapper
  migrationWrap: async (payload: any, mode: string = 'sha3_256') => {
    const res = await client.post('/api/migration/wrap', { payload, mode });
    return res.data;
  },

  migrationVerify: async (wrapped_message: any, mode: string = 'sha3_256') => {
    const res = await client.post('/api/migration/verify', { wrapped_message, mode });
    return res.data;
  },

  // Attacks
  simulateTampering: async (message?: any) => {
    const res = await client.post('/api/attacks/tampering', message || null);
    return res.data;
  },

  simulateReplay: async (message?: any, delay_seconds: number = 400) => {
    const res = await client.post(`/api/attacks/replay?delay_seconds=${delay_seconds}`, message || null);
    return res.data;
  },

  simulateDowngrade: async (message?: any) => {
    const res = await client.post('/api/attacks/downgrade', message || null);
    return res.data;
  },

  simulateCollision: async () => {
    const res = await client.post('/api/attacks/collision');
    return res.data;
  },

  simulateMissingMetadata: async (message?: any) => {
    const res = await client.post('/api/attacks/missing-metadata', message || null);
    return res.data;
  },

  simulateInvalidTag: async (message?: any) => {
    const res = await client.post('/api/attacks/invalid-tag', message || null);
    return res.data;
  },

  simulateFirmwareMod: async (message?: any) => {
    const res = await client.post('/api/attacks/firmware-mod', message || null);
    return res.data;
  },

  // Risk
  getRiskAnalysis: async () => {
    const res = await client.get('/api/risk/analysis');
    return res.data;
  },

  // Dashboard
  getDashboardStats: async () => {
    const res = await client.get('/api/dashboard/stats');
    return res.data;
  },

  // Audit Logs
  getAuditLogs: async (limit: number = 50, offset: number = 0) => {
    const res = await client.get(`/api/audit/logs?limit=${limit}&offset=${offset}`);
    return res.data;
  },
};
