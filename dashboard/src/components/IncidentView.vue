<script setup>
import { computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { incidentExercise } from '../../fixtures/mlkem-incident.mjs';
import { assessCheckpoint, exerciseConnection } from '../../incident.mjs';
import { clockTime, customerReport, state } from '../dashboard.js';
import { statusLabels, utc } from '../display.js';

const roles = { security: 'Sarah · Security', migration: 'Michael · Migration', executive: 'Emma · Executive' };
const statuses = {
  affected: ['red', 'Simulated affected'],
  unknown: ['amber', 'Applicability unresolved'],
  pending: ['amber', 'Remediation pending'],
  verified: ['green', 'Simulated response verified'],
};

const route = useRoute();
const router = useRouter();
const role = computed(() => typeof route.query.role === 'string' && Object.hasOwn(roles, route.query.role) ? route.query.role : 'security');
const selected = computed({
  get: () => typeof route.query.checkpoint === 'string' && Object.hasOwn(incidentExercise.checkpoints, route.query.checkpoint)
    ? route.query.checkpoint : 'affected',
  set: value => router.replace({ query: { role: role.value, checkpoint: value } }),
});
const checkpoint = computed(() => incidentExercise.checkpoints[selected.value]);
const assessment = computed(() => assessCheckpoint(checkpoint.value));
const connection = computed(() => exerciseConnection(state.source, customerReport.value, state.snapshot?.connections ?? []));
const headline = computed(() => statuses[assessment.value.status]);
const actions = computed(() => {
  const { upgraded, rotated, checked, status } = assessment.value;
  const { inventory, rotation, continuity } = checkpoint.value;
  return [
    { title: 'Upgrade the provider', owner: 'Platform operations',
      status: upgraded ? 'Recorded' : status === 'unknown' ? 'Awaiting inventory' : 'Required',
      detail: upgraded ? inventory.ref : 'Confirm the fixed release before scheduling the update.' },
    { title: 'Rotate the long-term key and update the gateway pin', owner: 'Cloud and gateway operations',
      status: rotated ? 'Recorded' : 'Pending',
      detail: rotated ? rotation.ref : 'Coordinate the new public-key fingerprint with the gateway team before cutover.' },
    { title: 'Verify reconnection and monitoring', owner: 'Field operations',
      status: checked ? 'Recorded' : 'Pending',
      detail: checked ? continuity.ref : 'Check the new session and verify that pump telemetry reaches the cloud.' },
  ];
});
const executiveDecision = computed(() => ({
  affected: 'Approve a coordinated maintenance window and ask for reconnection and monitoring evidence before closure.',
  unknown: 'Assign platform operations to confirm the deployed version and ask Sarah for an updated assessment.',
  pending: 'Keep the incident open until key rotation, gateway pin change and monitoring recovery are recorded.',
  verified: 'Review residual historical exposure and confirm the next advisory review with Sarah.',
})[assessment.value.status]);

</script>

<template>
  <article class="panel incident-view" aria-label="Internal ML-KEM incident">
    <header class="incident-header">
      <span class="report-eyebrow">INTERNAL · COURSE EXERCISE</span>
      <h2>Advisory and response</h2>
      <p>Incident details stay internal. Emma owns any customer communication.</p>
    </header>

    <nav class="incident-roles" aria-label="Incident role">
      <RouterLink v-for="(label, key) in roles" :key="key" class="button"
        :aria-current="role === key ? 'page' : undefined" :to="{ name: 'incident', query: { role: key, checkpoint: selected } }">{{ label }}</RouterLink>
    </nav>

    <template v-if="connection">
      <div class="incident-toolbar">
        <label class="field-control"><span>Exercise checkpoint</span>
          <select v-model="selected"><option v-for="(item, key) in incidentExercise.checkpoints" :key="key" :value="key">{{ item.label }}</option></select>
        </label>
        <p>{{ customerReport.customer.name }}<br>Connection report as of <time>{{ utc(clockTime) }}</time></p>
      </div>
      <section class="incident-callout" :data-status="assessment.status" aria-label="Connection and implementation status">
        <span class="badge" :class="headline[0]" role="status">{{ headline[1] }}</span>
        <h3>{{ connection.id }} · {{ connection.device }} cloud link</h3>
        <p>Reported key establishment <strong>{{ connection.keyEstablishment }} · {{ statusLabels[connection.status] }}</strong></p>
        <p>Exercise evidence as of <time>{{ utc(checkpoint.asOf) }}</time></p>
        <RouterLink class="text-link" :to="{ name: 'evidence', params: { id: connection.id }, query: { from: 'incident', role, checkpoint: selected } }">Inspect connection evidence</RouterLink>
      </section>

      <section v-if="role === 'security'" class="incident-section">
        <h3>Applicability evidence</h3>
        <dl class="incident-facts">
          <div><dt>Provider and deployed version</dt><dd>{{ incidentExercise.provider }} · {{ assessment.version ?? 'Version evidence missing' }}</dd></div>
          <div><dt>Exercise advisory scope</dt><dd>{{ incidentExercise.affectedVersion }} affected · {{ incidentExercise.fixedVersion }} fixed</dd></div>
          <div><dt>Inventory source and age</dt><dd v-if="assessment.version">{{ checkpoint.inventory.ref }} · {{ utc(checkpoint.inventory.at) }} · {{ assessment.ageHours.toFixed(1) }} hours old</dd><dd v-else>Missing. Platform operations to confirm the provider version.</dd></div>
          <div><dt>Incident source</dt><dd>{{ incidentExercise.notice }}</dd></div>
        </dl>
        <p>Inventory and action records describe potential exposure and response. Timing observations, key recovery and past decryption are outside the available evidence.</p>
      </section>

      <section v-else-if="role === 'migration'" class="incident-section">
        <h3>Response and monitoring continuity</h3>
        <ol class="incident-actions">
          <li v-for="action in actions" :key="action.title">
            <div><strong>{{ action.title }}</strong><p>{{ action.owner }} · {{ action.detail }}</p></div>
            <span class="badge" :class="action.status === 'Recorded' ? 'green' : 'amber'">{{ action.status }}</span>
          </li>
        </ol>
        <p>A cutover can interrupt pump monitoring. Coordinate with field operations and keep the 2027 migration target and 2028 replacement gap visible.</p>
      </section>

      <section v-else class="incident-section">
        <h3>Executive decision</h3>
        <p><strong>Emma · Review at the next internal incident checkpoint.</strong> {{ executiveDecision }}</p>
        <ul class="incident-risks">
          <li><strong>Exposure:</strong> Historical traffic protected by potentially exposed keys remains a risk to assess.</li>
          <li><strong>Continuity:</strong> Coordinate any remaining cutover work with pump monitoring.</li>
          <li><strong>Contract:</strong> Track the 2027 target alongside the 2028 replacement gap.</li>
        </ul>
      </section>
    </template>
    <section v-else class="incident-section">
      <h3>No matching exercise connection</h3>
      <p>The simulated connection is scoped to Northfield in the bundled demo dataset.</p>
      <RouterLink class="text-link" :to="{ name: 'customer' }">Choose customer scope</RouterLink> ·
      <RouterLink class="text-link" :to="{ name: 'snapshot' }">Open dataset settings</RouterLink>
    </section>

    <section class="incident-section">
      <h3>Repository and production scope</h3>
      <dl class="incident-facts">
        <div><dt>Browser dashboard · out of scope</dt><dd>Vue manifests and lockfile contain no ML-KEM provider. The page reads synthetic connection evidence.</dd></div>
        <div><dt>Gateway/Cloud prototype · pending</dt><dd><code>requirements.txt</code> pins <code>cryptography==50.0.1</code>. A local Windows wheel check reported OpenSSL 4.0.2. The course notice has no vendor or affected range to match.</dd></div>
        <div><dt>Production deployment · unknown</dt><dd>Deployment versions and the long-term key inventory are unavailable. Platform operations would collect them for Sarah's review.</dd></div>
        <div><dt>Earlier notice · proposed check</dt><dd>Sarah to review provider advisories after dependency changes and at the next sprint review, with platform operations recording version matches.</dd></div>
      </dl>
      <a class="text-link" href="https://cryptography.io/en/latest/changelog/#v50-0-1">Cryptography release notes</a> ·
      <a class="text-link" href="https://openssl-library.org/news/vulnerabilities/">OpenSSL advisory index</a>
    </section>
  </article>
</template>

<style src="../incident.css"></style>
