import "../node_modules/picnic/picnic.min.css";
import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import VueAuthHref from 'vue-auth-href';


const app = createApp(App);

app.use(VueAuthHref);

app.mount('#app');
