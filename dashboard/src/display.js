export const statusLabels = { pqc: 'PQC', fallback: 'Fallback', unknown: 'Unknown' };
export const segmentLabels = {
  'device-to-gateway': 'Device → gateway',
  'gateway-to-cloud': 'Gateway → cloud',
};

export function utc(value) {
  return new Date(value).toISOString().replace('T', ' ').replace(/\.\d{3}Z$/, ' UTC');
}
