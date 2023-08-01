import { createRouter, createWebHistory } from 'vue-router';
import { getWithExpiry } from '../store';

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
            path: '/admin',
            name: 'admin',
            component: () => import('../views/Admin.vue'),
        },
        {
            path: '/access_log',
            name: 'access_log',
            component: () => import('../views/Card.vue'),
        },
        {
            path: '/print',
            name: 'dayticket_print',
            component: () => import('../views/Print.vue'),
        },
        {
            path: '/scanner',
            name: 'scanner',
            component: () => import('../views/Scanner.vue'),
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
        return { name: 'login', query: { next: to.name } }
    }
})

export default router