import { createApp } from 'vue';
import "../node_modules/picnic/picnic.min.css";
import App from './App.vue';
import router from './router';
import './style.css';

const app = createApp(App);

app.use(router);

app.mount('#app');
