import { createRouter, createWebHashHistory } from 'vue-router';
import CoverageOverview from './components/CoverageOverview.vue';
import RolePanel from './components/RolePanel.vue';
import ConnectionInventory from './components/ConnectionInventory.vue';
import EvidenceView from './components/EvidenceView.vue';
import SnapshotView from './components/SnapshotView.vue';
import MethodologyView from './components/MethodologyView.vue';

export const destinations = [
  { path: '/', name: 'overview', label: 'Overview', title: 'Migration overview', icon: 'overview', component: CoverageOverview },
  { path: '/security', name: 'security', label: 'Security', title: 'Security review', icon: 'shield', component: RolePanel, props: { role: 'security' } },
  { path: '/migration', name: 'migration', label: 'Migration', title: 'Migration planning', icon: 'trend', component: RolePanel, props: { role: 'migration' } },
  { path: '/executive', name: 'executive', label: 'Executive', title: 'Executive briefing', icon: 'brief', component: RolePanel, props: { role: 'executive' } },
  { path: '/connections', name: 'connections', label: 'Connections', title: 'Connection inventory', icon: 'links', component: ConnectionInventory },
  { path: '/snapshot', name: 'snapshot', label: 'Dataset', title: 'Snapshot settings', icon: 'database', component: SnapshotView },
  { path: '/methodology', name: 'methodology', label: 'Methodology', title: 'Interpretation guide', icon: 'book', component: MethodologyView },
];

export const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    ...destinations.map(({ label, title, icon, ...record }) => ({ ...record, meta: { title } })),
    { path: '/connections/:id', name: 'evidence', component: EvidenceView, meta: { title: 'Connection evidence' } },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
});
