import { createRouter, createWebHistory } from 'vue-router';
import { getWithExpiry, setWithExpiry } from '../store';

const isAuthenticated = function() {
 var access_token = getWithExpiry("access_token");
 return access_token ? true : false;
}

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: '/login',
            name: 'login',
            component: () => import('../views/Login.vue'),
        },
        {
            path: '/',
            name: 'card',
            component: () => import('../views/Card.vue'),
        },
        {
            path: '/access_log',
            name: 'access_log',
            component: () => import('../views/Card.vue'),
        },
        {
            path: '/dayticket_print',
            name: 'dayticket_print',
            component: () => import('../views/Card.vue'),
        }
    ],
    scrollBehavior(to, from, savedPosition) {
        if (savedPosition) {
            return savedPosition
        } else {
            return { top: 0 }
        }
    },
})

router.beforeEach(async (to, from) => {
    if (!isAuthenticated() && to.name !== 'login') {
        setWithExpiry("redirect_path", to.path, 3600 * 1000);
        return { name: 'login' }
    }
})

export default router