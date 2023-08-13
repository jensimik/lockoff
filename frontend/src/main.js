import { createApp } from 'vue';
import "../node_modules/picnic/picnic.min.css";
import App from './App.vue';
import router from './router';
import './style.css';
import * as Sentry from "@sentry/vue";


Sentry.init({
    Vue,
    dsn: "https://642cb9b1809b78966c6047f962af4aad@o4504589908377600.ingest.sentry.io/4505697343373312",
    integrations: [
      new Sentry.BrowserTracing({
        // Set 'tracePropagationTargets' to control for which URLs distributed tracing should be enabled
        tracePropagationTargets: ["localhost", "https://lockoff-api.gnerd.dk"],
        routingInstrumentation: Sentry.vueRouterInstrumentation(router),
      }),
      new Sentry.Replay(),
    ],
    // Performance Monitoring
    tracesSampleRate: 1.0, // Capture 100% of the transactions, reduce in production!
    // Session Replay
    replaysSessionSampleRate: 0.1, // This sets the sample rate at 10%. You may want to change it to 100% while in development and then sample at a lower rate in production.
    replaysOnErrorSampleRate: 1.0, // If you're not already sampling the entire session, change the sample rate to 100% when sampling sessions where errors occur.
  });

const app = createApp(App);

app.use(router);

app.mount('#app');
