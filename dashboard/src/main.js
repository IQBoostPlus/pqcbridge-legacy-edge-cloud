import { createApp } from 'vue';
import App from './App.vue';
import { router } from './router.js';
import './styles.css';
import './responsive.css';
import './sprint2.css';

createApp(App).use(router).mount('#app');
